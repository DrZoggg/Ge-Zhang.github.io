# Scientific visual sources

These scenes are conceptual decorative artwork. They do not represent measurements,
patient trajectories, biological mechanisms, institutional facilities or live data.

## Celestial wheel adaptation

- Source: https://github.com/zaoxu001/celestial-wheel
- Pinned commit: `92523275172139b3f67f06a3fa080b4e4f0d4e3d`
- Copyright (c) 2026 zaoxu001; MIT License, reproduced at
  `../vendor/celestial-wheel-LICENSE`.
- `scenes.js` adapts the upstream XZ circle construction, concentric ring groups,
  independent quaternion poses, outer orbits and 36-degree perspective camera.
- Visual 4.1 adaptation: seven independently posed instrument carriers (three
  beveled primary bands and four secondary rings), three faint distant orbits,
  machined face grooves, fine radial ticks, localized highlight arcs and three
  nodes that move along their ring paths. A stable Fresnel glass shell contains
  an internal polyhedral cage, two fine tracks and a lit geometric nucleus.
- Continuous ring poses use a 32-second decorative phase; the node and internal
  structure speeds are independent. Lighting, depth fog, responsive framing,
  palette updates and bounded pointer parallax are site-specific additions.
- Removed: all cosmological text/data, glyph atlases, taiji, randomized disruptive
  events, picking, zoom/wheel handlers, global pointer listeners and per-scene RAF.
- Upstream used unlit basic materials and postprocessing; the directional and
  hemisphere lights here are new, not attributed to the upstream implementation.
- No code or images from the separately modified reference site are redistributed.

## Three.js

- Source: https://github.com/mrdoob/three.js/releases/tag/r186
- Release: r186 / 0.186.0, published 2026-09-24.
- Commit: `9b4a2ac29c63ccb43fd51c5661f2f873ac2c39b8`
- MIT License: `../vendor/three-r186/LICENSE`.
- Original official `build/three.module.js` and `build/three.core.js` are self-hosted,
  unmodified. This release no longer supplies minified build files. No CDN, addons,
  framework, model or texture dependency is loaded at runtime.

## Original implementation

`index.js` is a shared, visibility-aware lifecycle manager. `scenes.js` implements
an original spatial field: six fiber wave surfaces at distinct depths, six sparse
node clusters anchored to those surfaces, local and cross-depth network links,
a bounded implicit Schwarz-P-inspired perforated core with a lightly shaded skin
and internal geometry, GPU wave propagation and 24 moving trajectory samples.
All geometry is deterministic and generated locally. This is not a scientific
simulation, a measured knowledge graph or a visualization of the site's papers.

Both scenes expose `setPointer(x, y)` and accept active delta time in `update`.
Pointer movement is smoothed and bounded; no event listeners or animation loops
are created by the scene constructors. The shared manager owns input, timing,
pausing, visibility, quality and disposal. There are no postprocessing passes,
reflection captures, texture downloads or extra WebGL renderers.

The six transparent WebP posters are actual Edge/WebGL captures of these same
scenes at decorative time 4 seconds, in both palettes. They are not generated
images or borrowed reference artwork. They remain available without JavaScript,
WebGL, motion or data-saving permission. Test harnesses and recordings are kept
outside the production repository.

The field's narrow-layout pair keeps the center geometry unchanged and folds the
outer layers inward when the host aspect ratio is below 1.5. Its camera retains
the multi-layer field in a 346 by 260 CSS-pixel viewport. The six posters were
regenerated from Visual 4.1; desktop wheel is 680 by 620 pixels, desktop field is
1160 by 460 pixels and compact field is 346 by 260 pixels.
