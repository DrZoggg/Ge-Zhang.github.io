# Ge Zhang Academic GEO Website — Codex Engineering Instructions

## Role

You are the engineering executor for this repository.

Scientific research, biomedical interpretation, Paper GEO content design, numerical verification, and scientific source-of-truth are prepared outside Codex unless a task explicitly provides them.

Do not independently reinterpret, expand, exaggerate, or invent biomedical evidence.

The default project workflow is:

Web Chat
→ scientific research, verification, architecture, GEO/SEO/citation strategy, Gold Standard content
→ precise engineering instruction
→ Codex implementation, validation, Git delivery and deployment

Do not redo scientific research already supplied by Web Chat unless explicitly requested.

## Repository

Repository:

`DrZoggg/Ge-Zhang.github.io`

Canonical site:

`https://drgezhang.com/`

Local repository root:

`D:\CodexWork\张格GEO网站\Ge-Zhang.github.io`

This repository powers a high-trust, machine-readable, evidence-first Academic Evidence Hub.

Long-term objective:

Retrievable → Answerable → Verifiable → Citable

## Before Every Task

Always:

1. Fetch or inspect the current remote repository state.
2. Read current `origin/main`.
3. Confirm current local HEAD and working-tree status.
4. Never rely on stale SHA values or historical publication counts.
5. Treat current remote main as the engineering source of truth.
6. Inspect only files relevant to the requested task.
7. If the current repository state conflicts with task assumptions, stop and report the conflict before modifying files.

Do not perform broad repository exploration without a concrete engineering reason.

## Scientific Integrity

Scientific accuracy takes precedence over SEO, GEO, scoring tools, keyword coverage, visual polish, or automation.

Never:

- rewrite association as causation;
- rewrite prediction as treatment efficacy;
- present retrospective evidence as prospective clinical validation;
- present animal or cell evidence as human clinical evidence;
- present exploratory analysis as a confirmed mechanism;
- invent sample sizes, participant counts, specimen counts, cell counts, AUC, HR, OR, C-index, p-values, effect sizes, pathways, mechanisms, clinical claims, or validation results;
- perform keyword stuffing;
- fabricate unsupported authority or provenance;
- automatically rewrite biomedical evidence solely to improve GEO/SEO scores.

When exact scientific source-of-truth content is supplied by Web Chat, preserve it unless the task explicitly authorizes a scientific correction.

When scientific information is uncertain, preserve existing content and report the uncertainty rather than guessing.

## Default Protected Invariants

Unless a task explicitly authorizes a change, preserve:

- publication master records;
- publication title;
- journal;
- year;
- article type;
- DOI;
- authors;
- `citation_author`;
- slug;
- canonical URLs;
- indexed paper URLs;
- Featured / Selected Research membership and order;
- Deep GEO membership and order;
- Person identity;
- ORCID;
- Profile Control;
- Research Themes;
- sitemap URL inventory and lastmod semantics;
- ORCID synchronization;
- Crossref synchronization;
- IndexNow;
- GitHub Pages configuration and deployment pipeline.

Never treat historical counts as permanent invariants. Read current values from the current repository.

Featured / Selected Research and Deep GEO are independent control layers.

A Paper GEO upgrade must not automatically change membership or order.

## Architecture

Preserve the existing Scientific Evidence Publishing Core.

Do not migrate the site to al-folio, Academic Pages, HugoBlox, another site framework, or another publishing architecture unless explicitly requested.

Maintain backward compatibility whenever practical.

Paper GEO V1 and V2 may coexist.

Do not rewrite stable pipelines merely for code aesthetics.

Do not rename stable slugs, URLs, identifiers, or controllers without explicit approval.

## Open-Source First

For substantial new engineering capabilities, first determine whether the task already specifies an approved mature open-source solution.

If additional prior-art investigation is explicitly requested, evaluate:

- maintenance status;
- recent commits/releases;
- license;
- integration model;
- deployment requirements;
- CLI/library/API/MCP support;
- compatibility with the existing architecture;
- SEO/indexing risk.

Preference order:

mature direct reuse
→ component reuse
→ lightweight adaptation
→ custom implementation last

Do not introduce a major framework, dependency, external server, or architectural migration without explicit approval.

Do not blindly apply third-party GEO recommendations or automated rewriting.

## Structured Data

Structured data must remain consistent with visible content.

Do not:

- add unsupported facts only to JSON-LD;
- fabricate complete authorship;
- fabricate Organization entities;
- fabricate addresses, telephone numbers, contact points, FAQs, or other entities;
- make Schema claims stronger than visible scientific evidence.

Prioritize stable identity and scholarly metadata such as:

- Person;
- ScholarlyArticle;
- author;
- DOI;
- datePublished;
- journal/publisher;
- concepts;
- citation metadata.

Only introduce more complex entity modeling when explicitly requested and justified.

## Paper GEO Engineering

Paper GEO pages are evidence landing pages, not marketing pages.

When implementing supplied Paper GEO source-of-truth, preserve:

- Publication Identity;
- Research Question;
- Author Evidence Summary;
- Study Profile / Evidence Snapshot;
- Key Findings;
- quantitative evidence;
- How the Study Was Done;
- What This Study Adds;
- Evidence Scope;
- Q&A;
- Concept & Entity Layer;
- Related Research;
- Provenance.

Preserve:

- HTML / Markdown parity;
- evidence references;
- source locators;
- related DOI resolution;
- citation metadata;
- JSON-LD consistency;
- provenance links.

Do not manufacture a synthetic total `n` when datasets represent different participants, specimens, tissues, or cells.

Do not alter supplied scientific source-of-truth content unless explicitly instructed.

## Engineering Style

Prefer:

- targeted patches;
- minimal diffs;
- existing repository patterns;
- backward-compatible changes;
- single-purpose commits;
- deterministic generation;
- idempotent build behavior.

Avoid:

- unrelated cleanup;
- opportunistic refactoring;
- broad repository scanning;
- renaming stable files;
- touching files outside task scope;
- rewriting working code solely for style;
- adding speculative features.

If a task can be solved safely with a small patch, use a small patch.

## Testing Strategy

Testing must be proportional to engineering risk.

### Small metadata, documentation, or presentation-only changes

Prefer:

- focused validation;
- relevant validator;
- targeted tests;
- diff review.

Do not run the full regression suite merely by habit.

### Renderer, schema, generator, publication pipeline, synchronization, or framework changes

Use as appropriate:

- baseline;
- build;
- validation;
- relevant/full regression suite;
- idempotence;
- before/after diff review;
- protected-invariant checks.

### Scientific Paper GEO upgrades

Validate, as relevant:

- exact scientific numbers;
- DOI;
- authors;
- URL;
- HTML/Markdown parity;
- JSON-LD consistency;
- evidence refs;
- source locators;
- related DOI resolution;
- membership/order invariants.

Quality comes first, but avoid redundant testing that does not reduce material risk.

## Git Workflow

Default workflow:

1. Fetch `origin`.
2. Read current remote `main`.
3. Ensure local repository state is understood.
4. Apply only the requested changes.
5. Run risk-proportionate validation.
6. Review the final diff.
7. Create one single-purpose commit unless explicitly instructed otherwise.
8. Never force push.
9. Push only after validation passes.
10. Verify remote final SHA.
11. Verify GitHub Pages deployment when the task affects deployed content or the workflow is triggered.

If remote `main` changes during execution, re-evaluate before delivery.

Use the authenticated GitHub CLI / Git Data API / available Git transport as appropriate.

Do not repeatedly retry a broken transport mechanism when an authenticated safe alternative is available.

## Efficiency

Quality is the first priority.

Within that constraint, minimize unnecessary:

- token usage;
- model reasoning time;
- network calls;
- repository scans;
- repeated research;
- repeated full regressions.

Do not:

- repeat scientific research already supplied by Web Chat;
- independently search papers when exact source-of-truth is supplied;
- scan the whole repository without need;
- rerun unrelated tests;
- redesign an already specified task;
- produce long narrative execution reports.

Prefer:

targeted patch
→ risk-proportionate validation
→ diff review
→ single commit
→ delivery

## GEO / SEO Tooling

Third-party GEO scores are diagnostic signals, not project objectives.

Do not change the site solely to increase a third-party score.

Do not automatically add:

- keyword stuffing;
- hidden AI instructions;
- prompt injection;
- invisible text;
- fake authority signals;
- unsupported FAQ schema;
- fabricated entities;
- speculative AI discovery endpoints.

Only implement tooling that genuinely improves crawlability, retrievability, semantic clarity, evidence density, citation readiness, entity identity, provenance, or machine-readable scholarly structure.

## Execution Speed

For routine engineering tasks:

- default to direct execution rather than extended planning;
- do not narrate routine intermediate steps;
- only interrupt the user when blocked, an invariant fails, or an approval is required;
- avoid repeated repository scans;
- fetch remote once at task start and recheck once immediately before delivery;
- if direct Git HTTPS transport fails once with a connectivity error, switch immediately to an authenticated safe API transport rather than retrying the same route;
- do not rerun tests whose result cannot materially affect the requested change;
- prefer targeted validation over full regression for low-risk changes;
- reuse verified source-of-truth supplied by Web Chat rather than researching it again.

Validation:

- only `AGENTS.md` may change
- no site build or regression suite is required
- run `git diff --check`
- review the exact diff

Commit:
`docs: optimize Codex execution speed`

Push to `main`.

If Pages is automatically triggered by the push, only observe and report the result.

## Final Report

Unless the task requests otherwise, keep the final report concise.

Report:

- starting SHA;
- final SHA;
- modified files;
- tests/validation performed;
- protected invariants;
- push status;
- GitHub Pages deployment status when relevant.

Do not include verbose chain-of-thought or unnecessary execution narration.
