#!/usr/bin/env python3

import feedparser
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

def normalize_title(title):
    """normalize title for duplicate detection"""
    return re.sub(r'[^\w\s]', '', title.lower()).strip()

def get_base_url(url):
    """extract base URL (domain/subdomain) from a feed URL"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def convert_to_canonical_url(original_url, canonical_base_url, regex_pattern=None):
    """convert URL to use canonical domain and apply optional regex transformation"""
    # parse the canonical base URL to get the domain
    canonical_parsed = urlparse(canonical_base_url)
    canonical_domain = f"{canonical_parsed.scheme}://{canonical_parsed.netloc}"
    
    # parse the original URL
    original_parsed = urlparse(original_url)
    
    # extract just the path without query parameters
    clean_path = original_parsed.path
    
    # apply regex pattern if provided
    if regex_pattern:
        try:
            # assume the regex pattern is in the format "search_pattern->replacement"
            if '->' in regex_pattern:
                search_pattern, replacement = regex_pattern.split('->', 1)
                clean_path = re.sub(search_pattern.strip(), replacement.strip(), clean_path)
            else:
                # if no replacement specified, assume we want to extract the first capture group
                match = re.search(regex_pattern, clean_path)
                if match and match.groups():
                    clean_path = '/' + match.group(1)
        except re.error:
            # if regex fails, use original path
            pass
    
    # construct the canonical URL
    return f"{canonical_domain}{clean_path}"

def parse_feed_entry(feed_entry):
    """parse a feed entry in format 'name|url|regex_pattern' or 'name|url' or just 'url'"""
    parts = feed_entry.split('|')
    
    if len(parts) >= 3:
        # format: "name|url|regex_pattern"
        name = parts[0].strip()
        url = parts[1].strip()
        regex_pattern = parts[2].strip() if parts[2].strip() else None
        return name, url, regex_pattern
    elif len(parts) == 2:
        # format: "name|url"
        name = parts[0].strip()
        url = parts[1].strip()
        return name, url, None
    else:
        # format: just "url" - use domain as name
        url = feed_entry.strip()
        parsed = urlparse(url)
        # use the domain as the name
        name = parsed.netloc.replace('www.', '')
        return name, url, None

def fetch_posts_from_feed(feed_url, source_name, base_url, regex_pattern=None):
    """fetch and parse RSS feed"""
    feed = feedparser.parse(feed_url)
    posts = []
    
    for entry in feed.entries:
        # parse date - handle different date formats
        published_date = None
        if hasattr(entry, 'published'):
            try:
                # try standard RSS format with timezone offset
                published_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d')
            except ValueError:
                try:
                    # try RSS format with timezone abbreviation
                    published_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d')
                except ValueError:
                    try:
                        # try ISO format
                        published_date = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d')
                    except ValueError:
                        published_date = 'Unknown'
        
        # convert link to canonical URL using the feed's base URL and regex pattern
        canonical_link = convert_to_canonical_url(entry.link, base_url, regex_pattern)
        
        post = {
            'title': entry.title,
            'link': canonical_link,
            'published': published_date or 'Unknown',
            'source': source_name,
            'source_url': base_url,
            'normalized_title': normalize_title(entry.title)
        }
        posts.append(post)
    
    return posts

def merge_and_deduplicate_posts(feeds_posts, max_posts=10):
    """merge posts from multiple feeds, remove duplicates based on order precedence"""
    all_posts = []
    seen_titles = set()
    
    # process feeds in order (first feed takes precedence)
    for feed_posts in feeds_posts:
        for post in feed_posts:
            if post['normalized_title'] not in seen_titles:
                all_posts.append(post)
                seen_titles.add(post['normalized_title'])
    
    # sort by published date (most recent first), handle 'Unknown' dates
    def sort_key(post):
        if post['published'] == 'Unknown':
            return '1900-01-01'  # put unknown dates at the end
        return post['published']
    
    all_posts.sort(key=sort_key, reverse=True)
    
    return all_posts[:max_posts]

def generate_blog_section(posts):
    """generate HTML section for blog posts"""
    section = "    <ul>\n"
    
    for post in posts:
        date_str = post['published'] if post['published'] != 'Unknown' else ''
        date_prefix = f"<span>{date_str}</span> " if date_str else ""
        section += f"      <li>{date_prefix}<a href=\"{post['link']}\" target=\"_blank\">{post['title']}</a></li>\n"
    
    section += "    </ul>"
    return section

def update_html(posts):
    """update index.html with latest blog posts"""
    try:
        with open('index.html', 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        print("index.html not found")
        return False
    
    blog_section = generate_blog_section(posts)
    
    # find the placeholder and replace existing blog posts
    placeholder = "<!-- BLOG_POSTS_PLACEHOLDER - Do not remove this comment -->"
    
    if placeholder in content:
        # remove any existing blog posts after the placeholder
        pattern = re.compile(f'{re.escape(placeholder)}.*?(?=\n  </section>)', re.DOTALL)
        new_content = pattern.sub(f"{placeholder}\n{blog_section}", content)
    else:
        print("Warning: BLOG_POSTS_PLACEHOLDER not found in index.html")
        return False
    
    # only write if content changed
    if new_content != content:
        with open('index.html', 'w', encoding='utf-8') as file:
            file.write(new_content)
        print("index.html updated with latest blog posts")
        return True
    else:
        print("No changes needed")
        return False

def main():
    # hardcoded feed URLs with optional regex patterns
    feed_entries = [
        "Medium|https://blog.zepedro.com/feed|/@[^/]+/(.+)",
        "Developers@Mews|https://developers.mews.com/author/jose-silva/feed/"
    ]
    
    # hardcoded max_posts
    max_posts = 25
    
    print(f"Fetching up to {max_posts} blog posts from {len(feed_entries)} feeds")
    
    try:
        # parse feed entries and fetch posts from all feeds
        feeds_posts = []
        for feed_entry in feed_entries:
            source_name, feed_url, regex_pattern = parse_feed_entry(feed_entry)
            base_url = get_base_url(feed_url)
            posts = fetch_posts_from_feed(feed_url, source_name, base_url, regex_pattern)
            feeds_posts.append(posts)
            print(f"Fetched {len(posts)} posts from {source_name}")
        
        # merge and deduplicate
        all_posts = merge_and_deduplicate_posts(feeds_posts, max_posts)
        
        if all_posts:
            updated = update_html(all_posts)
            if updated:
                print(f"Updated index.html with {len(all_posts)} blog posts")
                # show breakdown by source
                source_counts = {}
                for post in all_posts:
                    source_counts[post['source']] = source_counts.get(post['source'], 0) + 1
                for source, count in source_counts.items():
                    print(f"{source} posts: {count}")
            else:
                print("index.html is already up to date")
        else:
            print("No posts found in the feeds")
    except Exception as e:
        print(f"Error updating blog posts: {e}")
        exit(1)

if __name__ == "__main__":
    main()