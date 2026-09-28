# Decisions

The choices behind Homeward Trail, written as the answers I'd give if asked about them.

### Why is the whole game one HTML file with no build step?

Because the audience is anyone with a browser, including people who'll never clone a repo. One file can be opened by double-clicking, hosted on GitHub Pages as-is, and shared as a single attachment. The trade-off is a long file, so it's organized into clearly labelled sections (scenery, characters, obstacles, audio, UI), and there's a debug hook, `window.HomewardTrail._internals`, that lets tests drive the game frame by frame.

### Why generate the art and audio in code instead of shipping assets?

It keeps the project tiny, license-clean and consistent. Characters, buildings and landmarks are built from simple 3D shapes with flat toon shading and inflated back-face "ink" outlines; signs and textures are drawn on canvases; music, sound effects and the cartoon voices are synthesized with the Web Audio API. An early version used the browser's text-to-speech, but it sounded robotic and differed between browsers, so the voices are now sung syllables run through vowel filters, with a speech bubble so the words are still readable.

### How do you know every obstacle pattern can actually be escaped?

I don't trust eyeballing it. A simple bot plays full runs through the debug hook, and early on its crashes exposed a real bug: an overlapping "slalom" of trains could leave no reachable lane. That pattern was rebuilt as a weaving corridor where the open lane only ever moves one step at a time, with a switch window where both lanes are open. The bot now routinely reaches home, and the crashes it still has come from its own simple rules (like changing lanes mid-jump), not from impossible layouts.

### The game stuttered at the start on a laptop. What was wrong?

Two things. First, every roadside prop had been built with *all* of its stage variants (a barn, a cabin, a windmill, an aspen grove, a whole Capitol...) and simply hidden the ones it didn't need. That meant about 13,000 objects whose matrices were updated every frame. Props now build a variant only the first time their stage needs it, which brought the scene down to about 1,000 objects and cut matrix updates roughly tenfold. Second, frames were capped in a way that turned slow frames into slow motion. The loop now takes small physics substeps so the game keeps real-time speed, shaders are compiled up front, and if frames stay slow the renderer steps down resolution and shadow quality on its own.

### Why is scenery hidden far ahead instead of when a landmark appears?

Landmarks like Red Rocks need open space around them. Hiding nearby props at the moment the landmark spawned made rocks vanish in plain view. Because every landmark sits at a known distance, each prop now decides whether it belongs when it's recycled far beyond the fog. The check script tracks every prop across a full run and fails if anything changes visibility on screen.

### Why do stages change exactly at their signs?

In play-testing, the "Farmland" banner showed up while the screen still showed downtown. Props used to take on whatever stage the player was in when they were placed far ahead. Now each prop is dressed for the stage at the exact spot where it will stand, and sky and ground colours blend over a short stretch around each border, so the new area begins at its welcome sign.

### Why does Red Rocks look like a travel poster instead of a scale model?

An earlier version modelled the real bowl closely (long curved rows between two huge monoliths, raised up on a hill), but from a runner's-eye view it read as a wall of rock and it sat too far from the road. Play-testers responded to the classic poster look instead: one enormous layered slab behind straight terraces of red benches, a red-roofed stage right by the road, round green trees and a packed crowd. The band is four cartoon musicians (singer, guitarist, bassist and a drummer on a riser) with modern hair and hats, deliberately unlike the single long-haired guitarist on many posters. Only the venue's own footprint is cleared of scenery, so the red rocks on the approach stay put.

### How are the nonprofits presented, and why that way?

The goal is to inform without lecturing or slowing the game down. Each nonprofit gets a highway-style exit sign placed where it makes geographic sense (for example, The Wild Animal Sanctuary on the plains near Keenesburg), and a short card appears for nine seconds as you pass. The full showcase comes after the reunion, when the player has time to read. Descriptions were checked against public sources, only names are used (no logos), and there's a clear non-affiliation note.

### What went into accessibility and comfort?

Keyboard and touch controls, a mute toggle that's remembered, auto-pause when the tab loses focus, respect for reduced-motion settings, and menus that scroll or compact on short screens so every button stays reachable (a sideways phone used to hide the Play button). The pace was tuned down over play-testing so there's time to read the cards, and the scenic stretches around landmarks carry only snacks, never obstacles.
