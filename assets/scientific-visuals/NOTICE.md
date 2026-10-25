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
- Changed for this site: eight scientific-instrument rings, deterministic smooth
  32-second poses, material lighting and depth fog, palette updates, sparse ticks,
  curved highlights, a wire core, responsive camera and complete disposal.
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
an original coherent field: four sampled fiber sheets, a bounded implicit
Schwarz-P-inspired multiply perforated core, low-amplitude GPU deformation and
24 moving trajectory samples. This is not a scientific simulation.

The six transparent WebP posters are actual Edge/WebGL captures of these same
scenes at decorative time 4 seconds, in both palettes. They are not generated
images or borrowed reference artwork. They remain available without JavaScript,
WebGL, motion or data-saving permission. Test harnesses and recordings are kept
outside the production repository.

The field's narrow-layout pair keeps the center geometry unchanged and folds only
the outer fibers inward. Its responsive camera is reframed to retain all four
flows in a 346 by 260 CSS-pixel viewport; the desktop composition is unchanged.
