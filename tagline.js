const taglines = [
    "Software architect, technical lead, passionate developer, compulsive tester, usability geek, tinkerer, wannabe barista.",
    "Code whisperer, team navigator, obsessive optimizer, bug hunter, interface dreamer, hobbyist inventor, coffee enthusiast.",
    "Digital craftsman, agile captain, code poet, bug banisher, design perfectionist, perpetual tinkerer, caffeine devotee.",
    "System designer, solution weaver, relentless debugger, UX admirer, gadget tinkerer, and part-time coffee chemist.",
    "Architect of code, builder of teams, refactor addict, test addict, interface fan, maker of things, coffee connoisseur.",
    "Creative coder, collaborative captain, problem solver, bug eliminator, UI wizard, side-project aficionado, coffee philosopher.",
    "Technical storyteller, development guide, error eradicator, pixel pusher, gadget fiddler, coffee brewmaster in training.",
    "Software sculptor, agile navigator, bug slayer, UX enthusiast, tinkering hobbyist, coffee lab experimenter.",
    "Code architect, team motivator, detail obsessive, usability nerd, lifelong learner, coffee aficionado.",
    "Framework builder, sprint leader, problem whisperer, edge-case detective, design advocate, gadget explorer, espresso devotee.",
    "Digital dreamer, scrum master, testing fanatic, UX explorer, maker of gizmos, wannabe expresso artist.",
    "Code crafter, innovation driver, QA loyalist, interface nerd, tool hacker, roaster apprentice.",
    "System strategist, debugging detective, refactor wizard, UX hobbyist, weekend tinkerer, espresso adventurer.",
    "Software designer, code philosopher, bug crusher, user advocate, gizmo lover, amateur barista.",
    "Technical storyteller, error hunter, modular magician, interaction dreamer, idea tinkerer, coffee perfectionist.",
    "Solution strategist, pattern enthusiast, code troubleshooter, usability seeker, gizmo tweaker, coffee daydreamer.",
    "Development guru, code caretaker, quality champion, UI admirer, innovation seeker, espresso scholar.",
    "Software builder, agile shepherd, test enthusiast, bug eliminator, pixel enthusiast, coffee aficionado-in-training.",
    "System crafter, task master, relentless debugger, user-centered thinker, weekend DIYer, espresso apprentice.",
    "Creative coder, innovation guide, bug buster, design fanatic, gadget builder, cafeine driven dreamer.",
    "Tech visionary, development coach, detail hunter, usability fan, playful inventor, coffee lab tinkerer."
];
  
window.onload = function() {
    const el = document.getElementById("tagline");
    const idx = Math.floor(Math.random() * taglines.length);
    el.textContent = taglines[idx];
};