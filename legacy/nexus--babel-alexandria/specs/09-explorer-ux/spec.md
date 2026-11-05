# Explorer UX -- Specification

> **Domain:** 09-explorer-ux
> **Status:** Draft
> **Last updated:** 2026-02-23
> **Source of truth:** `src/nexus_babel/main.py`, `src/nexus_babel/frontend/templates/shell.html`

---

## Overview

The Explorer UX domain covers the interactive frontend for Nexus Babel Alexandria -- the interface through which users browse the corpus, visualize branch evolution timelines, explore the hypergraph knowledge structure, and monitor governance policy decisions. The frontend is a server-rendered Jinja2 shell with vanilla JavaScript that communicates with the `/api/v1/*` backend endpoints via `fetch()` calls authenticated by a user-provided API key stored in `localStorage`.

Currently, the system has a single `shell.html` template that renders all four views (corpus, hypergraph, timeline, governance) with basic data display: document listings, JSON dumps of hypergraph neighborhoods, branch replay output, and policy decision tables. There is no JavaScript framework, no bundled static assets, no component system, no search/filter capability, no interactive visualization, and no responsive mobile layout beyond a single CSS media query breakpoint.

The vision extends this into a full interactive portal with: a corpus browser supporting document drill-down to the atom level with search and filtering; an interactive hypergraph visualization with zoom, pan, and node/edge exploration; a timeline view with event playback and branch comparison; a governance dashboard with mode status indicators and audit trails; interaction nodes where users can trigger remixes, evolutions, and analyses from the UI; and an admin panel for API key management.

This domain depends on all backend domains (01-ingestion-atomization through 08-platform-infrastructure) being functional, as every frontend view consumes their API endpoints.

---

## User Stories

### P1 -- As-Built (Verified)

#### US-UX-01: Shell Template Rendering

> As a **user**, I want to navigate to `/app/{view}` and see a rendered HTML page with the correct view title and navigation so that I can access different aspects of the system.

**Given** the application is running
**When** I navigate to `/app/corpus`, `/app/hypergraph`, `/app/timeline`, or `/app/governance`
**Then**:
- The Jinja2 template `shell.html` is rendered with `{{ view }}` set to the requested view (`main.py:103-108`)
- The page title reads `"Nexus Babel Alexandria - {View|capitalize}"` (`shell.html:6`)
- The navigation bar highlights the current view with an `active` CSS class (`shell.html:170-174`)
- The page has a 2-column grid layout: main workspace panel (1.7fr) + ops monitor sidebar (1fr) (`shell.html:93-96`)
- Jinja2Templates uses the directory `src/nexus_babel/frontend/templates/` (`main.py:31`)

**Code evidence:** `main.py:103-108` (route handler), `shell.html:1-357` (full template).

#### US-UX-02: Unknown View Rejection

> As the **system**, I want to reject requests for unknown views so that only valid views are served.

**Given** a request to `/app/unknown_view`
**When** the route handler checks the `allowed` set
**Then**:
- The handler returns HTTP 404 with body "Not Found" (`main.py:106-107`)
- The `allowed` set is `{"corpus", "hypergraph", "timeline", "governance"}` (`main.py:105`)

**Code evidence:** `main.py:105-107`.

#### US-UX-03: Root Redirect to Corpus

> As a **user**, I want the root URL `/` to redirect me to the corpus view so that I have a default landing page.

**Given** the application is running
**When** I navigate to `/`
**Then** I receive a 307 redirect to `/app/corpus` (`main.py:91-93`)

**Code evidence:** `main.py:91-93`.

#### US-UX-04: API Key Management in Browser

> As a **user**, I want to enter, save, and clear my API key in the browser so that I can authenticate against protected endpoints without re-entering my key on each visit.

**Given** the shell template is rendered
**When** I interact with the API key controls
**Then**:
- A password input field (`#apiKey`) accepts the key (`shell.html:164`)
- The "Save" button stores the key in `localStorage` under the key `"nexus_api_key"` and triggers a refresh of all data (`shell.html:337-341`)
- The "Clear" button removes the key from `localStorage` and triggers a refresh (`shell.html:342-347`)
- On page load, the stored key is restored to the input field (`shell.html:350`)
- The `api()` helper function attaches the key as `X-Nexus-API-Key` header on every fetch call (`shell.html:213-215`)

**Code evidence:** `shell.html:192-210` (key functions), `shell.html:337-354` (event handlers + boot).

#### US-UX-05: Global Status and Whoami Display

> As a **user**, I want to see the system health status, my authenticated identity, and recent jobs in the sidebar so that I can monitor system state.

**Given** the shell template is rendered and an API key is configured
**When** the page loads and `loadGlobal()` runs
**Then**:
- `/healthz` is fetched (no auth) and displays "System healthy" or "System degraded" (`shell.html:232-239`)
- `/api/v1/auth/whoami` is fetched and displays `role`, `owner`, and `allowed_modes` (`shell.html:240`)
- `/api/v1/jobs?limit=12` is fetched and displays recent jobs as a list of `job_type + status + job_id` cards (`shell.html:241-243`)
- If any fetch fails (e.g., no API key), the sidebar shows "Auth/API unavailable" with the error message and prompts to set an API key (`shell.html:244-248`)

**Code evidence:** `shell.html:230-249`.

#### US-UX-06: Corpus View -- Document Listing with Metrics

> As a **user**, I want the corpus view to show document counts and a list of ingested documents so that I can see what is in the corpus.

**Given** I am on the corpus view (`/app/corpus`) with a valid API key
**When** `renderCorpus()` runs
**Then**:
- `GET /api/v1/documents` is fetched (`shell.html:252`)
- Three metric cards are displayed: "Total docs", "Ingested", "Projected" (`shell.html:258-262`)
- A fourth metric card shows "Conflicts" count (`shell.html:263`)
- Up to 40 documents are listed as cards showing filename (extracted from path), modality, ingest_status, and graph_projection_status (`shell.html:264-268`)
- Documents are listed in the order returned by the API (created_at ascending)

**Code evidence:** `shell.html:251-269`.

#### US-UX-07: Hypergraph View -- Integrity and Neighborhood

> As a **user**, I want the hypergraph view to show integrity information and a neighborhood sample for the first ingested document so that I can verify graph consistency.

**Given** I am on the hypergraph view (`/app/hypergraph`) with a valid API key and at least one ingested document
**When** `renderHypergraph()` runs
**Then**:
- `GET /api/v1/documents` is fetched and the first ingested, non-conflicted document is selected (`shell.html:272-273`)
- If no ingested document exists, "No ingested document available." is displayed (`shell.html:274-276`)
- `GET /api/v1/hypergraph/documents/{id}/integrity` and `GET /api/v1/hypergraph/query?document_id={id}&limit=30` are fetched in parallel (`shell.html:278-280`)
- Three metric cards show: "Document nodes", "Atom nodes", "Consistent" (yes/no) (`shell.html:282-286`)
- A neighborhood sample is displayed as prettified JSON (`shell.html:288`)

**Code evidence:** `shell.html:271-290`.

#### US-UX-08: Timeline View -- Branch Listing and Replay

> As a **user**, I want the timeline view to show branches and replay/compare results so that I can explore the evolution history.

**Given** I am on the timeline view (`/app/timeline`) with a valid API key
**When** `renderTimeline()` runs
**Then**:
- `GET /api/v1/branches?limit=24` is fetched (`shell.html:293`)
- If no branches exist, a message directs the user to create one via API (`shell.html:295-297`)
- The first branch is replayed via `POST /api/v1/branches/{id}/replay` and the result is displayed as JSON (`shell.html:300, 307`)
- If two or more branches exist, the first two are compared via `GET /api/v1/branches/{id}/compare/{other}` and the diff is displayed as JSON (`shell.html:302-304`)
- Up to 20 branches are listed as cards showing id, mode, branch_version, and root_document_id (`shell.html:309-312`)

**Code evidence:** `shell.html:292-314`.

#### US-UX-09: Governance View -- Policy Decision History

> As a **user**, I want the governance view to show recent policy decisions so that I can audit content governance.

**Given** I am on the governance view (`/app/governance`) with a valid API key (operator role or higher)
**When** `renderGovernance()` runs
**Then**:
- `GET /api/v1/audit/policy-decisions?limit=24` is fetched (`shell.html:317`)
- Decisions are listed as cards showing mode, allow status, policy hits, audit_id, and decision_trace as JSON (`shell.html:318-323`)

**Code evidence:** `shell.html:316-323`.

#### US-UX-10: View Error Handling

> As a **user**, I want to see clear error messages when a view fails to load so that I understand what went wrong.

**Given** any view encounters an API error
**When** the rendering function throws
**Then**:
- The `renderView()` catch block displays a red-styled error message: "Failed to load {view}: {error.message}" (`shell.html:332-334`)
- The sidebar continues to function independently of view loading

**Code evidence:** `shell.html:325-335`.

#### US-UX-11: CSS Design System

> As a **user**, I want the application to have a consistent visual design so that the interface feels cohesive.

**Given** the shell template is rendered
**Then**:
- CSS custom properties define the design system: `--ink` (text), `--paper` (background), `--panel` (card), `--line` (border), `--accent` (teal), `--accent-2` (purple), `--warn` (red), `--ok` (green) (`shell.html:8-17`)
- Typography uses IBM Plex Sans for headings and IBM Plex Mono for body/code (`shell.html:17-18`)
- Cards use `.panel` class with 14px border-radius, subtle box-shadow, white background (`shell.html:97-103`)
- Navigation uses pill-shaped links with border-radius 999px (`shell.html:78-79`)
- A radial gradient background gives subtle depth to the page (`shell.html:26-28`)
- A single `@media (max-width: 980px)` breakpoint collapses to single-column layout (`shell.html:152-155`)

**Code evidence:** `shell.html:7-156` (all CSS).

#### US-UX-12: No-Auth Route Access

> As the **system**, I want the frontend shell, healthz, and metrics routes to be accessible without authentication so that users can load the page before entering an API key.

**Given** no authentication
**When** I request `/app/corpus`, `/healthz`, or `/metrics`
**Then** all three respond with HTTP 200 without requiring an API key (`main.py:91-108`; these routes are not wrapped in `_require_auth`)

**Code evidence:** `main.py:91-108` (no `Depends(_require_auth)` on these routes).

### P2 -- Partially Built

#### US-UX-13: Static Assets Serving

> As a **developer**, I want to serve static CSS and JavaScript files from a `/static/` path so that the frontend can use external assets.

**Current state:** FastAPI has `StaticFiles` support but it is not mounted in `create_app()`. All CSS and JS are currently inlined in `shell.html`. No `static/` directory exists.

**Gap:** No `app.mount("/static", StaticFiles(directory="..."), name="static")` call. No static directory structure.

#### US-UX-14: Responsive Layout for Tablets

> As a **user**, I want the layout to work well on tablet-sized screens so that I can use the application on various devices.

**Current state:** A single `@media (max-width: 980px)` breakpoint collapses the 2-column grid to 1 column (`shell.html:152-155`). The API key input width adjusts. No other responsive adaptations exist.

**Gap:** No intermediate breakpoints (e.g., 768px for tablet). No touch-optimized interactions. No mobile navigation pattern (hamburger menu, bottom nav).

### P3+ -- Vision

#### US-UX-15: Corpus Browser with Document Drill-Down

> As a **user**, I want to click on a document in the corpus list and see its full detail including atom breakdown, provenance, variant links, and cross-modal links so that I can explore document structure in depth.

**Vision:**
- Document detail panel shows all fields from `GET /api/v1/documents/{id}` including title, modality, checksum, size, provenance JSON
- Atom breakdown by level: counts per level (glyph-seed, syllable, word, sentence, paragraph) with expandable lists
- Glyph-seed inspector: select individual glyph-seeds to view phoneme_hint, historic_forms, visual_mutations, thematic_tags, future_seeds
- Variant links section showing sibling representations and semantic equivalences
- Cross-modal link section showing linked media files with click-to-navigate
- Back button to return to the document list

**API dependencies:** `GET /api/v1/documents/{id}` (exists), atom-level query endpoint (not yet built).

#### US-UX-16: Corpus Search and Filter

> As a **user**, I want to search and filter the corpus by modality, ingest status, conflict flag, and text content so that I can find specific documents.

**Vision:**
- Filter bar with dropdowns for modality (text, pdf, image, audio, binary) and ingest_status (pending, parsed, ingested, unchanged, conflict)
- Checkbox toggles for `conflict_flag` and `graph_projection_status`
- Text search across document paths and titles (client-side filter initially, server-side search endpoint later)
- Active filter indicators with clear-all option
- Result count display

**API dependencies:** `GET /api/v1/documents` (exists but returns all -- filtering is client-side only). Server-side search endpoint (not yet built).

#### US-UX-17: Interactive Hypergraph Visualization

> As a **user**, I want an interactive graph visualization where I can zoom, pan, click nodes, and follow edges so that I can explore the knowledge structure visually.

**Vision:**
- Force-directed graph layout using a library (D3.js force simulation, vis.js, Cytoscape.js, or Sigma.js)
- Document nodes as larger circles, atom nodes as smaller dots, colored by atom_level
- CONTAINS edges drawn between document and atom nodes
- Click on a node to see its details in a side panel
- Zoom and pan controls
- Node/edge count limits with pagination or level-of-detail control
- Filter by atom_level to show only specific layers
- Search by node ID or content substring
- Optional: force simulation controls (strength, distance, collision radius)

**API dependencies:** `GET /api/v1/hypergraph/query` (exists with document_id, node_id, relationship_type, limit params).

#### US-UX-18: Timeline Visualization with Event Playback

> As a **user**, I want an interactive timeline showing branch evolution with event playback so that I can understand how text evolves over time.

**Vision:**
- Vertical or horizontal timeline showing branches as tracks and events as nodes on each track
- Event types color-coded: natural_drift (green), synthetic_mutation (purple), phase_shift (orange), glyph_fusion (red), remix (blue)
- Click an event to see its diff_summary, event_payload, and before/after text preview
- "Play" button to step through events sequentially, showing the text evolving
- Branch comparison side-by-side view with diff highlighting
- Branch tree visualization showing parent-child relationships
- Phase indicator showing current evolution phase (expansion/peak/compression/rebirth)

**API dependencies:** `GET /api/v1/branches` (exists), `GET /api/v1/branches/{id}/timeline` (exists), `POST /api/v1/branches/{id}/replay` (exists), `GET /api/v1/branches/{id}/compare/{other}` (exists).

#### US-UX-19: Governance Dashboard with Mode Indicator

> As a **user**, I want a governance dashboard showing the current mode (PUBLIC/RAW), policy decision history with filtering, and audit statistics so that I can understand and monitor content governance.

**Vision:**
- Mode indicator: large badge showing current mode (PUBLIC = green, RAW = amber)
- Policy decision table with columns: timestamp, mode, allow/block, policy hits, audit_id
- Filter by mode, allow/block status, date range
- Decision detail panel with full decision_trace JSON and the evaluated text
- Statistics: total decisions, block rate, most frequent policy hits
- Audit log viewer for governance-related actions

**API dependencies:** `GET /api/v1/audit/policy-decisions` (exists), `GET /api/v1/auth/whoami` (provides mode info).

#### US-UX-20: Interaction Nodes -- Trigger Operations from UI

> As an **operator**, I want to trigger ingestion, analysis, evolution, remix, and governance evaluation directly from the UI so that I do not need to use curl or another HTTP client.

**Vision:**
- **Corpus view:** "Ingest" button to trigger `POST /api/v1/ingest/batch` with file selector
- **Corpus view:** "Analyze" button on each document to trigger `POST /api/v1/analyze`
- **Timeline view:** "Evolve Branch" form to trigger `POST /api/v1/evolve/branch` with event type selector and payload editor
- **Timeline view:** "Remix" form to trigger `POST /api/v1/remix` with source/target selectors and strategy picker
- **Governance view:** "Evaluate Text" form to trigger `POST /api/v1/governance/evaluate` with text input and mode selector
- **Seed corpus:** "Provision Seed" button to trigger `POST /api/v1/corpus/seed`
- All operations show inline progress indicators and results

**API dependencies:** All mutation endpoints (already exist).

#### US-UX-21: Admin API Key Management Panel

> As an **admin**, I want to manage API keys (list, create, disable, set roles and raw_mode) from the UI so that I do not need direct database access.

**Vision:**
- Accessible only to admin-role users (hidden/disabled for lower roles)
- List all API keys with owner, role, enabled status, raw_mode_enabled, last_used_at
- Create new API key form: owner name, role selector, raw_mode toggle
- Disable/enable toggle per key
- Generated key shown once on creation with copy-to-clipboard
- Delete key (with confirmation)

**API dependencies:** Key management endpoints (not yet built -- requires new routes).

#### US-UX-22: Thread Scaffold and Conversation Management

> As a **user**, I want conversation threads attached to documents and branches so that I can annotate, discuss, and track analytical observations over time.

**Vision:**
- Thread panel on document detail and branch timeline views
- Create new thread with title and initial message
- Add messages to existing threads
- Thread tagging (analysis, evolution, remix, governance)
- Thread search and filter

**API dependencies:** Thread/comment endpoints (not yet built).

#### US-UX-23: JavaScript Component Architecture

> As a **developer**, I want the frontend to use a component-based architecture so that views are maintainable and testable.

**Vision:**
- Either a lightweight framework (Alpine.js, htmx, Lit, Preact) or vanilla Web Components
- Each view as a self-contained component with its own state management
- Shared components: data table, metric card, JSON viewer, modal dialog, form controls
- Component tests via a test runner (Vitest, Playwright component tests)
- CSS extracted to external stylesheets with component-scoped styles

**API dependencies:** None (architectural concern).

---

## Functional Requirements

### Shell and Navigation

- **FR-UX-001** [MUST]: The system MUST serve a Jinja2-rendered HTML page at `GET /app/{view}` for each view in the set `{corpus, hypergraph, timeline, governance}`. *Implemented in `main.py:103-108`.*

- **FR-UX-002** [MUST]: The system MUST return HTTP 404 for any view not in the allowed set. *Implemented in `main.py:105-107`.*

- **FR-UX-003** [MUST]: `GET /` MUST redirect to `/app/corpus`. *Implemented in `main.py:91-93`.*

- **FR-UX-004** [MUST]: The navigation bar MUST highlight the current view with a visually distinct style (`.active` class). *Implemented in `shell.html:170-174`.*

- **FR-UX-005** [MUST]: Frontend routes (`/app/{view}`, `/`, `/healthz`, `/metrics`) MUST NOT require authentication. *Implemented in `main.py:91-108` (no `_require_auth` dependency).*

- **FR-UX-006** [SHOULD]: The system SHOULD serve static assets (CSS, JS, images) from a `/static/` mount point. *Not yet implemented.*

- **FR-UX-007** [SHOULD]: The navigation SHOULD include the brand name "Nexus Babel-Alexandria" and an "Internal Alpha" indicator. *Implemented in `shell.html:161`.*

### API Key Management (Browser-Side)

- **FR-UX-008** [MUST]: The frontend MUST provide an API key input field, a Save button, and a Clear button in the header. *Implemented in `shell.html:162-167`.*

- **FR-UX-009** [MUST]: The Save button MUST store the API key in `localStorage` under key `"nexus_api_key"`. *Implemented in `shell.html:204-206, 337-341`.*

- **FR-UX-010** [MUST]: The Clear button MUST remove the API key from `localStorage`. *Implemented in `shell.html:208-210, 342-347`.*

- **FR-UX-011** [MUST]: On page load, the stored API key MUST be restored to the input field. *Implemented in `shell.html:350`.*

- **FR-UX-012** [MUST]: All `fetch()` calls to `/api/v1/*` endpoints MUST include the stored key as `X-Nexus-API-Key` header. *Implemented in `shell.html:213-215`.*

- **FR-UX-013** [SHOULD]: The API key input SHOULD use `type="password"` to mask the value. *Implemented in `shell.html:164`.*

- **FR-UX-014** [MAY]: The frontend MAY provide a "test key" button that calls `/api/v1/auth/whoami` and displays the result. *Not yet implemented.*

### Global Status Sidebar

- **FR-UX-015** [MUST]: The sidebar MUST display system health from `GET /healthz` as "System healthy" (green) or "System degraded" (red). *Implemented in `shell.html:232-239`.*

- **FR-UX-016** [MUST]: The sidebar MUST display the authenticated user's role, owner, and allowed modes from `GET /api/v1/auth/whoami`. *Implemented in `shell.html:240`.*

- **FR-UX-017** [MUST]: The sidebar MUST display up to 12 recent jobs from `GET /api/v1/jobs?limit=12` with job_type and status. *Implemented in `shell.html:241-243`.*

- **FR-UX-018** [MUST]: If API calls fail (no key or invalid key), the sidebar MUST show "Auth/API unavailable" with the error message. *Implemented in `shell.html:244-248`.*

### Corpus View

- **FR-UX-019** [MUST]: The corpus view MUST fetch and display the document list from `GET /api/v1/documents`. *Implemented in `shell.html:251-269`.*

- **FR-UX-020** [MUST]: The corpus view MUST show summary metrics: total documents, ingested count, projected count, and conflict count. *Implemented in `shell.html:257-263`.*

- **FR-UX-021** [MUST]: Each document row MUST show the filename (extracted from path), modality, ingest_status, and graph_projection_status. *Implemented in `shell.html:264-268`.*

- **FR-UX-022** [MUST]: The corpus view MUST limit the displayed list to 40 documents. *Implemented in `shell.html:264`.*

- **FR-UX-023** [SHOULD]: The corpus view SHOULD support pagination to display more than 40 documents. *Not yet implemented.*

- **FR-UX-024** [SHOULD]: The corpus view SHOULD support filtering by modality and ingest_status. *Not yet implemented.*

- **FR-UX-025** [SHOULD]: Clicking a document row SHOULD navigate to or expand a document detail panel showing full provenance, atom counts by level, and variant links. *Not yet implemented.*

- **FR-UX-026** [MAY]: The corpus view MAY display atom-level drill-down with glyph-seed metadata inspection. *Not yet implemented.*

### Hypergraph View

- **FR-UX-027** [MUST]: The hypergraph view MUST select the first ingested, non-conflicted document and display its integrity info. *Implemented in `shell.html:271-290`.*

- **FR-UX-028** [MUST]: The hypergraph view MUST display document nodes, atom nodes, and consistency status as metric cards. *Implemented in `shell.html:282-286`.*

- **FR-UX-029** [MUST]: The hypergraph view MUST display a neighborhood query result as formatted JSON. *Implemented in `shell.html:288`.*

- **FR-UX-030** [MUST]: If no ingested document exists, the hypergraph view MUST display "No ingested document available." *Implemented in `shell.html:274-276`.*

- **FR-UX-031** [SHOULD]: The hypergraph view SHOULD allow selecting which document to inspect (not just the first). *Not yet implemented.*

- **FR-UX-032** [SHOULD]: The hypergraph view SHOULD render an interactive graph visualization instead of raw JSON. *Not yet implemented.*

- **FR-UX-033** [MAY]: The hypergraph view MAY support filtering by atom_level, relationship_type, or content search. *Not yet implemented.*

### Timeline View

- **FR-UX-034** [MUST]: The timeline view MUST fetch and display branches from `GET /api/v1/branches?limit=24`. *Implemented in `shell.html:292-314`.*

- **FR-UX-035** [MUST]: The timeline view MUST replay the first branch via `POST /api/v1/branches/{id}/replay` and display the result as JSON. *Implemented in `shell.html:300, 307`.*

- **FR-UX-036** [MUST]: If two or more branches exist, the timeline view MUST compare the first two and display the diff as JSON. *Implemented in `shell.html:302-304`.*

- **FR-UX-037** [MUST]: If no branches exist, the timeline view MUST display a message directing the user to create one via API. *Implemented in `shell.html:295-297`.*

- **FR-UX-038** [MUST]: Each branch row MUST show id, mode, branch_version, and root_document_id. *Implemented in `shell.html:309-312`.*

- **FR-UX-039** [SHOULD]: Clicking a branch SHOULD display its full timeline from `GET /api/v1/branches/{id}/timeline`. *Not yet implemented.*

- **FR-UX-040** [SHOULD]: The timeline view SHOULD render events as a visual timeline (vertical or horizontal) rather than raw JSON. *Not yet implemented.*

- **FR-UX-041** [MAY]: The timeline view MAY support event playback with animated text evolution. *Not yet implemented.*

- **FR-UX-042** [MAY]: The timeline view MAY show branch tree visualization with parent-child relationships. *Not yet implemented.*

### Governance View

- **FR-UX-043** [MUST]: The governance view MUST fetch and display policy decisions from `GET /api/v1/audit/policy-decisions?limit=24`. *Implemented in `shell.html:316-323`.*

- **FR-UX-044** [MUST]: Each decision row MUST show mode, allow status, policy hits, audit_id, and decision_trace as JSON. *Implemented in `shell.html:318-323`.*

- **FR-UX-045** [SHOULD]: The governance view SHOULD show the current user's mode (PUBLIC/RAW) as a prominent badge. *Not yet implemented.*

- **FR-UX-046** [SHOULD]: The governance view SHOULD support filtering decisions by mode and allow/block status. *Not yet implemented.*

- **FR-UX-047** [MAY]: The governance view MAY show aggregate statistics (total decisions, block rate, frequent hits). *Not yet implemented.*

### Design System

- **FR-UX-048** [MUST]: The frontend MUST use CSS custom properties for theming: `--ink`, `--paper`, `--panel`, `--line`, `--accent`, `--accent-2`, `--warn`, `--ok`. *Implemented in `shell.html:8-17`.*

- **FR-UX-049** [MUST]: The frontend MUST use IBM Plex Sans for headings and IBM Plex Mono for body/code text. *Implemented in `shell.html:17-18`.*

- **FR-UX-050** [MUST]: The layout MUST use a 2-column CSS Grid that collapses to 1 column at 980px viewport width. *Implemented in `shell.html:93-96, 152-155`.*

- **FR-UX-051** [SHOULD]: The frontend SHOULD support at least one additional breakpoint (e.g., 768px) for tablet layouts. *Not yet implemented.*

- **FR-UX-052** [SHOULD]: The frontend SHOULD load IBM Plex fonts from a CDN or local assets rather than relying on system font fallbacks. *Not yet implemented (font-family declarations exist but no font loading).*

### Error Handling and Resilience

- **FR-UX-053** [MUST]: If a view's render function throws, the error MUST be caught and displayed inline with a red warning style. *Implemented in `shell.html:332-334`.*

- **FR-UX-054** [MUST]: The `api()` helper MUST parse JSON responses and throw on non-2xx status codes with the detail message. *Implemented in `shell.html:217-222`.*

- **FR-UX-055** [SHOULD]: The sidebar and view content SHOULD load independently so that a sidebar failure does not block the view. *Partially implemented: `loadGlobal()` and `renderView()` are called sequentially in `boot()` (`shell.html:349-354`).*

- **FR-UX-056** [SHOULD]: The frontend SHOULD show a loading indicator while data is being fetched. *Not yet implemented.*

### Interaction Nodes

- **FR-UX-057** [MAY]: The corpus view MAY include buttons to trigger ingestion and analysis operations. *Not yet implemented.*

- **FR-UX-058** [MAY]: The timeline view MAY include forms to trigger branch evolution and remix operations. *Not yet implemented.*

- **FR-UX-059** [MAY]: The governance view MAY include a form to evaluate text against policies. *Not yet implemented.*

- **FR-UX-060** [MAY]: The seed corpus section MAY include buttons to provision and ingest seed texts. *Not yet implemented.*

### Admin Panel

- **FR-UX-061** [MAY]: The system MAY provide an admin panel for API key management accessible only to admin-role users. *Not yet implemented.*

- **FR-UX-062** [MAY]: The admin panel MAY support creating, listing, enabling/disabling, and deleting API keys. *Not yet implemented.*

---

## Key Entities

### Frontend State (browser-side, in-memory)

| Variable | Type | Purpose |
|----------|------|---------|
| `currentView` | `string` | The active view name, injected by Jinja2 as `{{ view }}` |
| `nexus_api_key` | `string` (localStorage) | Persisted API key for authentication |
| `keyInput` | `HTMLInputElement` | DOM reference to the API key input |
| `statusEl` | `HTMLElement` | DOM reference for health status display |
| `whoamiEl` | `HTMLElement` | DOM reference for whoami display |
| `jobsPanelEl` | `HTMLElement` | DOM reference for jobs list in sidebar |
| `viewContentEl` | `HTMLElement` | DOM reference for main view content area |

### Consumed API Entities

The frontend does not define its own data models. It consumes and renders the following backend response shapes:

| Endpoint | Response Shape | Used In |
|----------|---------------|---------|
| `GET /healthz` | `{status: string}` | Sidebar health |
| `GET /api/v1/auth/whoami` | `{api_key_id, owner, role, raw_mode_enabled, allowed_modes}` | Sidebar whoami |
| `GET /api/v1/jobs` | `{jobs: [{job_id, job_type, status, ...}]}` | Sidebar jobs |
| `GET /api/v1/documents` | `{documents: [{id, path, modality, ingested, ingest_status, conflict_flag, atom_count, graph_projection_status, ...}]}` | Corpus view |
| `GET /api/v1/documents/{id}` | `{id, path, title, modality, provenance, ...}` | Corpus detail (P3) |
| `GET /api/v1/hypergraph/documents/{id}/integrity` | `{document_nodes, atom_nodes, consistent}` | Hypergraph metrics |
| `GET /api/v1/hypergraph/query` | `{count: {nodes, edges}, nodes: [...], edges: [...]}` | Hypergraph neighborhood |
| `GET /api/v1/branches` | `{branches: [{id, parent_branch_id, root_document_id, mode, branch_version}]}` | Timeline listing |
| `POST /api/v1/branches/{id}/replay` | `{branch_id, event_count, text_hash, preview, replay_snapshot}` | Timeline replay |
| `GET /api/v1/branches/{id}/compare/{other}` | `{left_branch_id, right_branch_id, left_hash, right_hash, distance, same, preview_left, preview_right}` | Timeline compare |
| `GET /api/v1/audit/policy-decisions` | `{decisions: [{mode, allow, policy_hits, audit_id, decision_trace}]}` | Governance view |
| `GET /api/v1/corpus/seeds` | `{seeds: [{title, author, language, source_url, local_path, atomization_status}]}` | Seed corpus (P3) |

---

## Edge Cases

### Covered by Current Implementation

- **EC-UX-01: No API key set.** All fetch calls to `/api/v1/*` fail with 401. The sidebar catches this and displays "Auth/API unavailable: Missing or invalid API key" (`shell.html:244-248`). View content shows the same error pattern (`shell.html:332-334`).

- **EC-UX-02: Invalid API key.** Same behavior as no key -- 401 triggers the error display path.

- **EC-UX-03: Unknown view path.** `/app/invalid` returns HTTP 404 with "Not Found" text body (`main.py:106-107`).

- **EC-UX-04: Empty corpus.** The corpus view shows "No items." via `renderRows()` when the documents list is empty (`shell.html:226`). Metric cards show 0 for all counts.

- **EC-UX-05: No branches.** The timeline view displays "No branches yet. Create one via API /api/v1/evolve/branch." (`shell.html:296`).

- **EC-UX-06: No ingested documents for hypergraph.** Displays "No ingested document available." (`shell.html:274-276`).

- **EC-UX-07: API JSON parse failure.** The `api()` helper catches parse errors and wraps raw text in `{raw: text}` (`shell.html:220`).

### Not Covered / Known Gaps

- **EC-UX-08: Viewer role accessing governance view.** The governance view calls `/api/v1/audit/policy-decisions` which requires operator role. A viewer will get a 403 error displayed inline, but there is no role-gated UI (the nav link is always visible).

- **EC-UX-09: Large document count.** The corpus view fetches all documents (`GET /api/v1/documents` has no pagination) but only displays 40. With thousands of documents, the fetch payload could be large and slow. No pagination support.

- **EC-UX-10: Large JSON in hypergraph/timeline.** Neighborhood queries and replay snapshots are displayed as prettified JSON using `JSON.stringify(data, null, 2)`. For large graphs, this could produce megabytes of text in a single `<pre>` block, degrading rendering performance.

- **EC-UX-11: Concurrent view/sidebar loading.** `boot()` calls `loadGlobal()` then `renderView()` sequentially. If `loadGlobal()` is slow, the view content is delayed. They could run in parallel.

- **EC-UX-12: localStorage unavailable.** Private browsing or blocked `localStorage` causes `getApiKey()` to throw. No try/catch around localStorage access.

- **EC-UX-13: Stale API key.** If a stored API key is disabled or deleted server-side, the frontend continues to send it. The user sees auth errors but is not prompted to clear and re-enter.

- **EC-UX-14: Template directory path.** The Jinja2Templates directory is hardcoded to `"src/nexus_babel/frontend/templates"` (`main.py:31`), which is relative to the working directory, not the package. Running from a different directory (e.g., installed package) breaks template resolution.

- **EC-UX-15: XSS via document paths.** Document paths are inserted into the DOM via template literals without escaping (`${d.path.split("/").pop()}`). If a path contains HTML characters, they would be rendered as markup. The current inline approach uses `innerHTML` assignment which does not auto-escape.

- **EC-UX-16: Font loading.** IBM Plex fonts are declared in `font-family` fallback chains but no font files are loaded. The browser will use "Segoe UI" (Windows), "Menlo" (macOS), or system sans-serif as actual rendering font.

- **EC-UX-17: No keyboard navigation.** The shell template has no ARIA labels, skip links, or keyboard shortcuts. Tab order follows DOM order, which is functional but not optimized for accessibility.

---

## Success Criteria

| Criterion | Metric | Target |
|-----------|--------|--------|
| **View rendering** | All 4 views render without JavaScript errors when a valid API key is set | 100% view coverage |
| **Unknown view rejection** | `/app/anything_else` returns 404 | Verified |
| **Root redirect** | `/` redirects to `/app/corpus` | Verified |
| **API key persistence** | Key survives page reload via localStorage | Verified |
| **Error resilience** | Auth failures display clear messages in sidebar and view | All error paths handled |
| **Corpus metrics** | Total, ingested, projected, and conflict counts are accurate | Match API response |
| **Hypergraph integrity** | Document nodes, atom nodes, and consistency shown for first document | Correct values displayed |
| **Timeline replay** | First branch replayed and result shown | Valid JSON output |
| **Governance listing** | Recent policy decisions shown with mode and allow status | Matches API response |
| **CSS consistency** | All custom properties used, consistent card/nav styling | Visual audit |
| **Responsive breakpoint** | 980px breakpoint collapses to single column | Verified at 979px |
| **No-auth access** | `/app/*`, `/healthz`, `/metrics` accessible without API key | HTTP 200 for all |
| **P2: Static assets** | CSS and JS served from `/static/` | Mount point active, assets served |
| **P3: Document drill-down** | Click document to see detail with atom counts | Detail panel functional |
| **P3: Graph visualization** | Interactive graph with zoom/pan/click | Canvas or SVG rendered |
| **P3: Timeline viz** | Visual timeline with event playback | Timeline component rendered |
| **P3: Governance dashboard** | Mode badge, statistics, filtering | Dashboard functional |
| **P3: Interaction nodes** | Trigger operations from UI | At least 3 operations functional |
