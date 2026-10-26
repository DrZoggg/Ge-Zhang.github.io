# GradientWaves source and native adaptation notice

Original component: GradientWaves, React Bits, David Haz.
Repository: https://github.com/DavidHDev/react-bits
Fixed source commit: e12c22192ac7b4b452c5e2feb9b586d74765d696
Original files:
- src/content/Backgrounds/GradientWaves/GradientWaves.jsx
- src/content/Backgrounds/GradientWaves/GradientWaves.css

Copyright (c) 2026 David Haz.
License: MIT + Commons Clause License Condition v1.0. The complete original
license is retained in LICENSE.md in this directory. This is not plain MIT.
Use and modification as part of an application, website or product are permitted
subject to that license. Components themselves, including ported versions, must
not be sold, sublicensed or redistributed independently or in a component bundle.

Native adaptation changes (2026-10-26):
- Replaced only the React hooks/container wrapper with an explicit native renderer
  mount/update/render/dispose API, without React or additional runtime dependencies.
- Preserved the original VERTEX and FRAGMENT literal source, shader constants,
  analytic surface/lighting, rayAt/groundAt, parseColor, intro, swell envelope and
  adaptive ray-march stride math. The fragment template interpolates the original
  MAX_SWELLS=4 and CAMERA_HEIGHT=30 constants.
- Delegated RAF, DOM listeners, observers, visibility, reduced-motion preference
  observation and DPR selection to the owning website lifecycle wrapper.
- Added explicit delta/freeze rendering, state/CPU-submit metrics, phase-only
  setTime for local captures, initialization failure cleanup and idempotent disposal.
- resize dimensions are CSS pixels; DPR is explicitly passed by the caller.
  Pointer/swell coordinates are normalized 0..1. drawMs measures JavaScript/GL
  submission duration, not completed GPU execution or end-to-end frame duration.

This adaptation is integrated into the Ge Zhang website. It is not offered as a
standalone component, template pack, or component distribution service.
