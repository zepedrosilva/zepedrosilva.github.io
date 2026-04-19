#!/usr/bin/env python3

import feedparser
import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlparse

feedparser.USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


_BLOCK_TAGS = {
    'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'li', 'br', 'tr', 'blockquote', 'pre', 'figure', 'figcaption',
}


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fed = []

    def handle_starttag(self, tag, attrs):
        if tag in _BLOCK_TAGS:
            self.fed.append(' ')

    def handle_endtag(self, tag):
        if tag in _BLOCK_TAGS:
            self.fed.append(' ')

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def _strip_html(html):
    s = _HTMLStripper()
    s.feed(html)
    return s.get_data()


def get_entry_excerpt(entry):
    """Extract the article subtitle from a Medium RSS entry.

    Medium places the article deck/sub-heading in the first <h4> of the content.
    Falls back to the first <p> if no <h4> is present.
    """
    html = ''
    if hasattr(entry, 'content') and entry.content:
        html = entry.content[0].get('value', '')
    if not html:
        html = getattr(entry, 'summary', '')
    if not html:
        return ''

    # Medium subtitle is always the first <h4>
    h4 = re.search(r'<h4[^>]*>(.*?)</h4>', html, re.DOTALL | re.IGNORECASE)
    if h4:
        return _strip_html(h4.group(1)).strip()

    # Fallback: first non-empty <p>
    for p in re.finditer(r'<p[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE):
        text = _strip_html(p.group(1)).strip()
        if text:
            return text[:300].rsplit(' ', 1)[0] + ('\u2026' if len(text) > 300 else '')

    return ''


def normalize_title(title):
    return re.sub(r'[^\w\s]', '', title.lower()).strip()


def get_base_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def convert_to_canonical_url(original_url, canonical_base_url, regex_pattern=None):
    canonical_parsed = urlparse(canonical_base_url)
    canonical_domain = f"{canonical_parsed.scheme}://{canonical_parsed.netloc}"
    original_parsed = urlparse(original_url)
    clean_path = original_parsed.path

    medium_article_pattern = r'-([a-f0-9]{12})(?:\?|$)'
    match = re.search(medium_article_pattern, original_url)
    if match:
        article_id = match.group(1)
        return f"{canonical_domain}/{article_id}"

    if regex_pattern:
        try:
            if '->' in regex_pattern:
                search_pattern, replacement = regex_pattern.split('->', 1)
                clean_path = re.sub(search_pattern.strip(), replacement.strip(), clean_path)
            else:
                match = re.search(regex_pattern, clean_path)
                if match and match.groups():
                    clean_path = '/' + match.group(1)
        except re.error:
            pass

    return f"{canonical_domain}{clean_path}"


def parse_feed_entry(feed_entry):
    parts = feed_entry.split('|')
    if len(parts) >= 3:
        return parts[0].strip(), parts[1].strip(), parts[2].strip() or None
    elif len(parts) == 2:
        return parts[0].strip(), parts[1].strip(), None
    else:
        url = feed_entry.strip()
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', ''), url, None


def fetch_posts_from_feed(feed_url, source_name, base_url, regex_pattern=None):
    feed = feedparser.parse(feed_url)
    posts = []

    for entry in feed.entries:
        published_date = None
        if hasattr(entry, 'published'):
            for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %Z', '%Y-%m-%dT%H:%M:%S%z'):
                try:
                    published_date = datetime.strptime(entry.published, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue

        canonical_link = convert_to_canonical_url(entry.link, base_url, regex_pattern)

        posts.append({
            'title': entry.title,
            'link': canonical_link,
            'published': published_date or 'Unknown',
            'source': source_name,
            'source_url': base_url,
            'normalized_title': normalize_title(entry.title),
            'excerpt': get_entry_excerpt(entry),
        })

    return posts


def sort_posts_by_date(posts):
    posts.sort(key=lambda p: p['published'] if p['published'] != 'Unknown' else '1900-01-01', reverse=True)
    return posts


def generate_spotlight(post):
    """Generate the featured spotlight block for the latest post."""
    date_str = post['published'] if post['published'] != 'Unknown' else ''
    date_span = f'<span class="post-date">{date_str}</span>' if date_str else '<span class="post-date"></span>'
    excerpt_html = f'<p class="spotlight-excerpt">{post["excerpt"]}</p>' if post.get('excerpt') else ''
    return (
        f'      <a class="spotlight" href="{post["link"]}" target="_blank">'
        f'{date_span}'
        f'<div class="spotlight-body">'
        f'<span class="spotlight-title">{post["title"]}</span>'
        f'{excerpt_html}'
        f'</div>'
        f'<span class="post-arrow">↗</span>'
        f'</a>'
    )


def generate_blog_section(posts):
    """Generate the blog list for all posts except the spotlight (first) post."""
    section = '      <div class="blog-list">\n'
    for post in posts:
        date_str = post['published'] if post['published'] != 'Unknown' else ''
        date_span = f'<span class="post-date">{date_str}</span>' if date_str else '<span class="post-date"></span>'
        excerpt_html = f'<p class="post-excerpt">{post["excerpt"]}</p>' if post.get('excerpt') else ''
        section += (
            f'        <a class="post" href="{post["link"]}" target="_blank">'
            f'{date_span}'
            f'<div class="post-body">'
            f'<span class="post-title">{post["title"]}</span>'
            f'{excerpt_html}'
            f'</div>'
            f'<span class="post-arrow">↗</span>'
            f'</a>\n'
        )
    section += '      </div>'
    return section


def update_html(posts):
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("index.html not found")
        return False

    if not posts:
        print("No posts found in the feed")
        return False

    spotlight_placeholder = '<!-- BLOG_SPOTLIGHT_PLACEHOLDER - Do not remove this comment -->'
    list_placeholder = '<!-- BLOG_POSTS_PLACEHOLDER - Do not remove this comment -->'

    if spotlight_placeholder not in content or list_placeholder not in content:
        print("Warning: one or both placeholders not found in index.html")
        return False

    spotlight_html = generate_spotlight(posts[0])
    list_html = generate_blog_section(posts[1:])

    # Replace everything between spotlight placeholder and list placeholder
    new_content = re.sub(
        re.escape(spotlight_placeholder) + r'.*?' + re.escape(list_placeholder),
        f'{spotlight_placeholder}\n{spotlight_html}\n      {list_placeholder}',
        content,
        flags=re.DOTALL,
    )

    # Replace everything from list placeholder to end of section
    new_content = re.sub(
        re.escape(list_placeholder) + r'.*?(?=\n\s*</section>)',
        f'{list_placeholder}\n{list_html}',
        new_content,
        flags=re.DOTALL,
    )

    if new_content != content:
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"index.html updated — spotlight: 1 post, list: {len(posts) - 1} posts")
        return True
    else:
        print("No changes needed")
        return False


def main():
    feed_url = "https://medium.com/@zepedrosilva/feed"
    source_name = "Medium"
    base_url = "https://blog.zepedro.com"
    regex_pattern = "/@[^/]+/(.+)"

    print("Fetching blog posts from Medium")

    try:
        posts = fetch_posts_from_feed(feed_url, source_name, base_url, regex_pattern)
        print(f"Fetched {len(posts)} posts from {source_name}")
        sorted_posts = sort_posts_by_date(posts)
        update_html(sorted_posts)
    except Exception as e:
        print(f"Error updating blog posts: {e}")
        exit(1)


if __name__ == "__main__":
    main()
