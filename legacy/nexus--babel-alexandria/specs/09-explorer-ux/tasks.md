# Explorer UX -- Task List

## Phase 1: Setup and Foundation

### T-UX-001: Create static assets directory structure [P]

Set up the target directory structure for extracted CSS/JS. Mount static files in the FastAPI app factory.

- Create `src/nexus_babel/frontend/static/css/`, `src/nexus_babel/frontend/static/js/`, `src/nexus_babel/frontend/static/fonts/`
- Add `app.mount("/static", StaticFiles(directory="src/nexus_babel/frontend/static"), name="static")` to `create_app()` in `main.py`
- Verify `/static/` serves a test file (create a placeholder `static/css/README`)

**Files**: `src/nexus_babel/main.py`, `src/nexus_babel/frontend/static/` (new directory tree)
**Acceptance**: `GET /static/css/README` returns 200. No existing tests break.

### T-UX-002: Verify all 4 views render without JS errors [P]

Start the dev server, open each of the 4 views in a browser, and verify no console errors appear (with and without a valid API key). Document the current behavior as a baseline.

**Files**: (no file changes -- manual verification)
**Acceptance**: All 4 views load. Console errors documented if any.

### T-UX-003: Add a Playwright or pytest-based smoke test for frontend routes [P]

Create `tests/test_frontend_routes.py` that uses `TestClient` to verify:
- `GET /` returns 307 redirect to `/app/corpus`
- `GET /app/corpus` returns 200 with HTML containing "Corpus Workspace"
- `GET /app/hypergraph` returns 200 with HTML containing "Hypergraph Workspace"
- `GET /app/timeline` returns 200 with HTML containing "Timeline Workspace"
- `GET /app/governance` returns 200 with HTML containing "Governance Workspace"
- `GET /app/invalid` returns 404
- `GET /healthz` returns 200 with `{"status": "ok"}`
- `GET /metrics` returns 200 with JSON containing `"counters"` and `"timings"`

**Files**: `tests/test_frontend_routes.py` (new)
**Acceptance**: `pytest tests/test_frontend_routes.py -v` passes with 8+ tests.

---

## Phase 2: CSS Extraction and Design System

### T-UX-010: Extract CSS to external stylesheet [Story: US-UX-11]

Move all CSS from `shell.html` `<style>` block into `src/nexus_babel/frontend/static/css/design-system.css`. Replace the inline `<style>` with `<link rel="stylesheet" href="/static/css/design-system.css">`.

- Preserve all custom properties (`--ink`, `--paper`, etc.)
- Preserve all component classes (`.panel`, `.metric`, `.row`, `.list`, etc.)
- Preserve the `@media (max-width: 980px)` breakpoint
- Verify no visual regression by comparing before/after screenshots

**Files**: `src/nexus_babel/frontend/static/css/design-system.css` (new), `src/nexus_babel/frontend/templates/shell.html`
**Acceptance**: Page renders identically after extraction. CSS served from `/static/css/design-system.css`.

### T-UX-011: Add self-hosted IBM Plex font files [Story: US-UX-11] [P]

Download IBM Plex Sans and IBM Plex Mono WOFF2 files (regular + bold weights) and add `@font-face` declarations to the design system CSS.

- Download from Google Fonts or IBM's GitHub releases
- Place in `src/nexus_babel/frontend/static/fonts/`
- Add `@font-face` rules for `"IBM Plex Sans"` (400, 700) and `"IBM Plex Mono"` (400, 700)
- Verify fonts load by inspecting the browser's "Fonts" panel in DevTools

**Files**: `src/nexus_babel/frontend/static/fonts/*.woff2` (new), `src/nexus_babel/frontend/static/css/design-system.css`
**Acceptance**: DevTools shows IBM Plex fonts loaded (not fallback system fonts).

### T-UX-012: Add tablet breakpoint and responsive improvements [Story: US-UX-14]

Add a 768px breakpoint for tablet layouts:

- At 768px: collapse grid to single column, stack header elements vertically, full-width API key input
- At 480px: reduce font sizes, increase touch target sizes (min 44px height for buttons/links)
- Add `<meta name="viewport">` verification (already present)
- Test with browser DevTools responsive mode at 375px, 768px, 980px, 1280px

**Files**: `src/nexus_babel/frontend/static/css/design-system.css`
**Acceptance**: Layout works at all 4 breakpoints without horizontal scroll.

### T-UX-013: Add ARIA landmarks and accessibility basics [P]

Add semantic HTML and ARIA attributes:

- `<header role="banner">` (already has `<header>`)
- `<main role="main">` (already has `<main>`)
- `<aside role="complementary">` (already has `<aside>` inside `<main>`)
- `<nav role="navigation" aria-label="View navigation">`
- Add `aria-label="API key"` to the API key input
- Add a visually-hidden skip link: `<a href="#viewContent" class="skip-link">Skip to content</a>`
- Add `aria-live="polite"` to `#globalStatus` for screen reader updates

**Files**: `src/nexus_babel/frontend/templates/shell.html`
**Acceptance**: No axe-core critical violations when auditing the page.

---

## Phase 3: JavaScript Extraction and Enhancement

### T-UX-020: Extract JavaScript to external files [Story: US-UX-04, US-UX-05]

Move all `<script>` content from `shell.html` into organized external JS files:

- `src/nexus_babel/frontend/static/js/api.js` -- `NexusApiClient` class, `getApiKey()`, `setApiKey()`, `clearApiKey()`
- `src/nexus_babel/frontend/static/js/app.js` -- `boot()`, `loadGlobal()`, `renderView()`, event listeners
- `src/nexus_babel/frontend/static/js/views/corpus.js` -- `renderCorpus()`
- `src/nexus_babel/frontend/static/js/views/hypergraph.js` -- `renderHypergraph()`
- `src/nexus_babel/frontend/static/js/views/timeline.js` -- `renderTimeline()`
- `src/nexus_babel/frontend/static/js/views/governance.js` -- `renderGovernance()`
- Replace inline `<script>` with `<script src="/static/js/api.js">` + `<script src="/static/js/app.js">` etc.
- Use ES modules (`type="module"`) if targeting modern browsers, or plain scripts with explicit ordering
- Inject `currentView` via a `<script>` tag or `data-view` attribute on `<body>`

**Files**: `src/nexus_babel/frontend/static/js/*.js` (new), `src/nexus_babel/frontend/templates/shell.html`
**Acceptance**: All 4 views function identically after extraction. No inline `<script>` content remains except the `currentView` injection.

### T-UX-021: Add request timeout and error classification to API client [Story: US-UX-10]

Enhance the extracted `api.js`:

- Add `AbortController` with 15-second timeout
- Create `ApiError` class with `statusCode` and `message` fields
- Classify errors: 401 -> "auth_invalid", 403 -> "auth_forbidden", 404 -> "not_found", 500+ -> "server_error", network -> "network_error", timeout -> "timeout"
- Export error type constants for use in view renderers

**Files**: `src/nexus_babel/frontend/static/js/api.js`
**Acceptance**: Timeout triggers after 15s. Error types are correctly classified.

### T-UX-022: Add loading indicators [Story: US-UX-10]

Add visual feedback while data is loading:

- Create a reusable loading skeleton/spinner component in `src/nexus_babel/frontend/static/js/components/loading.js`
- Show skeleton placeholders in the view content area during `renderView()` execution
- Show a spinner or "Loading..." text in the sidebar during `loadGlobal()` execution
- Use CSS animation for the spinner (no external library)

**Files**: `src/nexus_babel/frontend/static/js/components/loading.js` (new), `src/nexus_babel/frontend/static/css/design-system.css`, `src/nexus_babel/frontend/static/js/app.js`
**Acceptance**: Loading indicator visible during slow API calls (can test by adding artificial delay).

### T-UX-023: Add localStorage error handling [P]

Wrap all `localStorage` access in try/catch to handle private browsing and other restrictions:

- `getApiKey()` returns `""` if localStorage throws
- `setApiKey()` silently fails if localStorage throws, with a console warning
- `clearApiKey()` silently fails if localStorage throws
- Add a one-time banner if localStorage is unavailable: "API key storage unavailable. Key will not persist."

**Files**: `src/nexus_babel/frontend/static/js/api.js`
**Acceptance**: No JavaScript errors in private browsing mode.

### T-UX-024: Fix XSS vulnerability in DOM rendering [P]

Replace all `innerHTML` assignments that include user data with safe alternatives:

- Use `textContent` for plain text values (document paths, error messages, status strings)
- Create a `safeHtml()` helper that escapes `<`, `>`, `&`, `"`, `'` characters
- Audit all template literal -> innerHTML assignments in view renderers
- Keep `innerHTML` only for structured HTML where all dynamic values pass through `safeHtml()`

**Files**: `src/nexus_babel/frontend/static/js/views/*.js`, `src/nexus_babel/frontend/static/js/app.js`
**Acceptance**: Document paths containing `<script>alert(1)</script>` render as plain text.

---

## Phase 4: Corpus View Enhancement (P2/P3)

### T-UX-030: Add client-side filtering to corpus view [Story: US-UX-16]

Add filter controls above the document list:

- Modality dropdown: All, text, pdf, image, audio, binary
- Status dropdown: All, pending, parsed, ingested, unchanged, conflict, ingested_with_warnings
- Conflict toggle: Show/hide conflicted documents
- Filters apply client-side to the already-fetched document list
- Active filter count displayed next to "Filter" label
- "Clear filters" button to reset all

**Files**: `src/nexus_babel/frontend/static/js/views/corpus.js`, `src/nexus_babel/frontend/static/css/views/corpus.css` (new)
**Acceptance**: Filters correctly reduce the displayed list. Clearing filters restores full list.

### T-UX-031: Add document detail panel [Story: US-UX-15]

Clicking a document row expands a detail panel below it (or replaces the list with a detail view):

- Fetch `GET /api/v1/documents/{id}` for full detail including provenance
- Display: title, modality, checksum, size_bytes, ingest_status, graph_projection_status
- Display provenance fields: extracted_text (first 500 chars), segments summary, raw_storage_path
- Display cross_modal_links if present
- Display atom_count with breakdown (requires counting from API -- initially show total only)
- Back button or click-to-collapse to return to list

**Files**: `src/nexus_babel/frontend/static/js/views/corpus.js`, `src/nexus_babel/frontend/static/css/views/corpus.css`
**Acceptance**: Clicking a document shows detail. Back button returns to list.

### T-UX-032: Add pagination to corpus view [Story: US-UX-16]

Replace the hard-coded 40-document limit with pagination:

- Show 25 documents per page
- "Previous" and "Next" buttons
- Page indicator: "Page 1 of 4 (100 documents)"
- Persist page number across filter changes (reset to page 1 on filter change)
- Client-side pagination of the fetched list (since the API returns all documents)

**Files**: `src/nexus_babel/frontend/static/js/views/corpus.js`, `src/nexus_babel/frontend/static/js/components/data-table.js` (new)
**Acceptance**: Pagination controls work correctly. Page resets on filter change.

### T-UX-033: Add seed corpus listing to corpus view [Story: US-UX-15]

Add a "Seed Texts" section below the document list:

- Fetch `GET /api/v1/corpus/seeds`
- Display each seed with title, author, language, atomization_status
- Color-code status: not_provisioned (gray), provisioned (green)
- P3 extension: "Provision" button for admin users calling `POST /api/v1/corpus/seed`

**Files**: `src/nexus_babel/frontend/static/js/views/corpus.js`
**Acceptance**: Seed texts displayed with correct statuses.

---

## Phase 5: Hypergraph View Enhancement (P3)

### T-UX-040: Add document selector to hypergraph view [Story: US-UX-17]

Replace the automatic "first ingested document" selection with a dropdown:

- Populate dropdown from `GET /api/v1/documents` (filter to ingested, non-conflicted)
- On selection change, fetch integrity and neighborhood for the chosen document
- Show "Select a document" placeholder when none selected
- Default to first document on initial load (current behavior preserved)

**Files**: `src/nexus_babel/frontend/static/js/views/hypergraph.js`
**Acceptance**: Dropdown lists all eligible documents. Selecting one refreshes the display.

### T-UX-041: Add graph visualization with vis.js [Story: US-UX-17]

Replace the JSON neighborhood dump with an interactive graph:

- Add vis.js Network library to `src/nexus_babel/frontend/static/vendor/` (or load from CDN)
- Create a `<div id="graphCanvas">` container in the hypergraph view
- Transform `hypergraph/query` response nodes/edges into vis.js DataSet format
- Document nodes: larger, blue circles with truncated path as label
- Atom nodes: smaller, colored by atom_level (glyph-seed=red, syllable=orange, word=green, sentence=blue, paragraph=purple)
- CONTAINS edges: light gray lines
- Enable zoom, pan, and drag
- On node click: display node properties in a side detail panel
- Limit initial render to 200 nodes (add "Load more" button)

**Files**: `src/nexus_babel/frontend/static/js/views/hypergraph.js`, `src/nexus_babel/frontend/static/css/views/hypergraph.css` (new), `src/nexus_babel/frontend/static/vendor/vis-network.min.js` (new)
**Acceptance**: Graph renders with colored nodes and edges. Zoom/pan/click works. Detail panel shows node info.

### T-UX-042: Add atom_level filter to graph visualization [Story: US-UX-17]

Add filter controls above the graph:

- Checkboxes for each atom_level: glyph-seed, syllable, word, sentence, paragraph
- Toggle visibility of atom nodes by level (hide/show, not re-fetch)
- "Show all" and "Hide all" convenience buttons
- Node count update when filters change

**Files**: `src/nexus_babel/frontend/static/js/views/hypergraph.js`
**Acceptance**: Toggling a level hides/shows its atoms. Node count updates.

---

## Phase 6: Timeline View Enhancement (P3)

### T-UX-050: Add branch selector and timeline fetch [Story: US-UX-18]

Replace the auto-replay of the first branch with an interactive branch selector:

- Branch dropdown populated from `GET /api/v1/branches`
- On selection, fetch `GET /api/v1/branches/{id}/timeline` and display events
- Event list with: event_index, event_type (color-coded badge), created_at
- Click event to see its event_payload and diff_summary in a detail panel

**Files**: `src/nexus_babel/frontend/static/js/views/timeline.js`, `src/nexus_babel/frontend/static/css/views/timeline.css` (new)
**Acceptance**: Branch dropdown works. Event list shows with correct types. Click shows detail.

### T-UX-051: Add visual timeline rendering [Story: US-UX-18]

Render events as a visual timeline using SVG or Canvas:

- Horizontal or vertical axis representing event sequence
- Event nodes positioned along the axis, spaced by event_index
- Event types color-coded: natural_drift=#15803d, synthetic_mutation=#9333ea, phase_shift=#d97706, glyph_fusion=#b91c1c, remix=#0ea5e9
- Hover to see event type and timestamp
- Click to select and show detail panel
- Current event highlighted with a border or glow effect

**Files**: `src/nexus_babel/frontend/static/js/views/timeline.js`, `src/nexus_babel/frontend/static/css/views/timeline.css`
**Acceptance**: SVG timeline renders with colored event nodes. Click selects event.

### T-UX-052: Add event playback to timeline [Story: US-UX-18]

Add playback controls for stepping through branch events:

- "Play" button: auto-advances through events at 1-second intervals
- "Pause" button: stops auto-advance
- "Previous" / "Next" buttons: manual step
- "Reset" button: return to first event
- Text preview area showing the evolving text at each event (from replay_snapshot or diff_summary)
- Playback indicator on the timeline showing current position

**Files**: `src/nexus_babel/frontend/static/js/views/timeline.js`
**Acceptance**: Play steps through events with text updates. Pause stops. Manual step works.

### T-UX-053: Add branch comparison UI [Story: US-UX-18]

Add a branch comparison panel:

- Two branch selectors (left and right)
- "Compare" button that calls `GET /api/v1/branches/{left}/compare/{right}`
- Display: distance, same/different indicator, side-by-side text previews
- Highlight differences in the preview text (character-level diff if feasible)

**Files**: `src/nexus_babel/frontend/static/js/views/timeline.js`
**Acceptance**: Two branches can be selected and compared. Distance and previews shown.

---

## Phase 7: Governance View Enhancement (P3)

### T-UX-060: Add mode indicator badge [Story: US-UX-19]

Add a prominent mode indicator to the governance view:

- Fetch mode info from `GET /api/v1/auth/whoami`
- Display mode as a large colored badge: PUBLIC=green with `--ok` color, RAW=amber
- Show the user's role alongside the mode indicator
- If RAW mode is not allowed, show "RAW: unavailable" in gray

**Files**: `src/nexus_babel/frontend/static/js/views/governance.js`, `src/nexus_babel/frontend/static/css/views/governance.css` (new)
**Acceptance**: Mode badge renders correctly for viewer (PUBLIC only) and researcher (PUBLIC + RAW).

### T-UX-061: Add decision filtering [Story: US-UX-19]

Add filter controls above the policy decision list:

- Mode filter: All, PUBLIC, RAW
- Status filter: All, ALLOW, BLOCK
- Client-side filtering of the fetched decision list
- Result count display
- Active filter indicator

**Files**: `src/nexus_babel/frontend/static/js/views/governance.js`
**Acceptance**: Filters correctly reduce the displayed list. Counts update.

### T-UX-062: Add governance evaluation form [Story: US-UX-20]

Add a form to evaluate text against policies:

- Text input (textarea)
- Mode selector: PUBLIC, RAW (RAW disabled if user lacks permission)
- "Evaluate" button that calls `POST /api/v1/governance/evaluate`
- Result display: allow/block badge, policy hits list, decision trace JSON

**Files**: `src/nexus_babel/frontend/static/js/views/governance.js`
**Acceptance**: Text can be submitted, result displayed inline. RAW mode disabled for non-researchers.

### T-UX-063: Add governance statistics panel [Story: US-UX-19]

Add an aggregate statistics section:

- Total decisions count
- Allow vs Block count (and percentage)
- Most frequent policy hits (top 5 terms)
- Computed client-side from the fetched decision list

**Files**: `src/nexus_babel/frontend/static/js/views/governance.js`
**Acceptance**: Statistics panel shows accurate counts derived from decision list.

---

## Phase 8: Interaction Nodes (P3)

### T-UX-070: Add "Analyze Document" button to corpus detail [Story: US-UX-20]

Add an "Analyze" button to the document detail panel (T-UX-031):

- Button visible only when user has operator+ role (check from whoami response)
- Clicking opens a modal with: layer checkboxes (all 9 layers pre-checked), mode selector, plugin profile selector
- "Run Analysis" calls `POST /api/v1/analyze` with the document_id
- Show inline result or redirect to analysis run detail

**Files**: `src/nexus_babel/frontend/static/js/views/corpus.js`, `src/nexus_babel/frontend/static/js/components/modal.js` (new)
**Acceptance**: Analysis triggers from UI. Result displayed.

### T-UX-071: Add "Evolve Branch" form to timeline view [Story: US-UX-20]

Add a form to create a new branch evolution:

- Root document selector (from corpus)
- Parent branch selector (optional, from branch list)
- Event type selector: natural_drift, synthetic_mutation, phase_shift, glyph_fusion
- Event payload editor (JSON textarea, pre-filled with example for selected type)
- Mode selector: PUBLIC, RAW
- "Evolve" button calls `POST /api/v1/evolve/branch`
- Result shows new_branch_id and event_id, refreshes branch list

**Files**: `src/nexus_babel/frontend/static/js/views/timeline.js`
**Acceptance**: Branch evolution triggers from UI. New branch appears in list.

### T-UX-072: Add "Remix" form to timeline view [Story: US-UX-20]

Add a remix form accessible from the timeline view:

- Source document/branch selector
- Target document/branch selector
- Strategy selector: interleave, thematic_blend, temporal_layer, glyph_collide
- Seed input (integer, default 0)
- Mode selector
- "Remix" button calls `POST /api/v1/remix`
- Result shows new_branch_id and diff_summary

**Files**: `src/nexus_babel/frontend/static/js/views/timeline.js`
**Acceptance**: Remix triggers from UI. New branch appears in list.

### T-UX-073: Add "Provision Seed" button for admins [Story: US-UX-20]

In the seed corpus section (T-UX-033):

- "Provision" button next to each unprovisioned seed (visible only to admin role)
- Clicking calls `POST /api/v1/corpus/seed` with the seed title
- Show spinner during provisioning, then update status to "provisioned"
- Handle errors (download failure, network timeout)

**Files**: `src/nexus_babel/frontend/static/js/views/corpus.js`
**Acceptance**: Admin can provision a seed text from the UI. Status updates after provisioning.

---

## Phase 9: Reusable Components (P3)

### T-UX-080: Create reusable data table component [P]

Build a sortable, filterable table component:

- Column definitions: `[{key, label, sortable, filterable, render}]`
- Client-side sorting by clicking column headers (asc/desc toggle)
- Client-side text filtering per column
- Pagination controls (configurable page size)
- Empty state message
- Used by: corpus view (document list), governance view (decision list), sidebar (job list)

**Files**: `src/nexus_babel/frontend/static/js/components/data-table.js` (new)
**Acceptance**: Component renders a table from data + column defs. Sort, filter, paginate work.

### T-UX-081: Create reusable JSON viewer component [P]

Build a collapsible JSON tree viewer:

- Renders JSON objects as expandable/collapsible tree nodes
- Keys displayed with syntax highlighting (strings=green, numbers=blue, booleans=purple, null=gray)
- Copy-to-clipboard button for the full JSON
- Used by: hypergraph neighborhood, timeline replay, governance decision trace

**Files**: `src/nexus_babel/frontend/static/js/components/json-viewer.js` (new)
**Acceptance**: JSON objects render as a tree. Nodes expand/collapse. Copy works.

### T-UX-082: Create reusable metric card component [P]

Formalize the existing `.metric` pattern as a component:

- Accepts: `{label, value, unit?, trend?, color?}`
- Renders a card with label (small) and value (large)
- Optional trend indicator (up/down arrow with percentage)
- Optional color for the value (e.g., red for conflicts)
- Used by: corpus metrics, hypergraph metrics, governance stats

**Files**: `src/nexus_babel/frontend/static/js/components/metric-card.js` (new)
**Acceptance**: Component renders correctly with all optional props.

### T-UX-083: Create reusable modal dialog component [P]

Build a modal dialog for forms and confirmations:

- Overlay with backdrop click to close
- Close button (X) in top-right
- Escape key to close
- Trap focus inside modal when open
- Title, body (slot/innerHTML), and footer (optional action buttons)
- Used by: analyze form, evolve form, remix form, seed provision confirmation

**Files**: `src/nexus_babel/frontend/static/js/components/modal.js` (new)
**Acceptance**: Modal opens, traps focus, closes on backdrop click/escape. Action buttons work.

---

## Phase 10: Cross-Cutting

### T-UX-090: Add Content Security Policy headers [P]

Add CSP headers to the FastAPI middleware:

- `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:;`
- Note: `'unsafe-inline'` for styles may be needed during transition. Remove after full CSS extraction.
- Verify no CSP violations in browser console

**Files**: `src/nexus_babel/main.py`
**Acceptance**: CSP header present on responses. No violations in console.

### T-UX-091: Add cache headers for static assets [P]

Configure cache headers for the static file mount:

- CSS/JS/fonts: `Cache-Control: public, max-age=3600, immutable` (1 hour)
- HTML templates: `Cache-Control: no-cache` (via middleware)
- Add cache-busting query parameter or versioned paths for production

**Files**: `src/nexus_babel/main.py` (middleware for cache headers)
**Acceptance**: Static files return correct `Cache-Control` headers.

### T-UX-092: Wire frontend smoke tests into CI [P]

Update CI workflow to run `pytest tests/test_frontend_routes.py -v` alongside existing tests.

**Files**: `.github/workflows/ci-minimal.yml`
**Acceptance**: CI passes with frontend route tests.

### T-UX-093: Add role-gated UI visibility [P]

Enhance the frontend to hide/disable features based on the authenticated user's role:

- Store whoami response in a global variable on page load
- Hide "Analyze" / "Evolve" / "Remix" buttons for viewer role
- Hide "Provision Seed" button for non-admin roles
- Disable governance view warning for viewers (governance decisions require operator)
- Show role badge in sidebar

**Files**: `src/nexus_babel/frontend/static/js/app.js`, all view JS files
**Acceptance**: Viewer sees read-only UI. Operator sees action buttons. Admin sees admin features.

### T-UX-094: Add parallel loading for sidebar and view content [P]

Refactor `boot()` to load sidebar and view content in parallel:

- Use `Promise.all([loadGlobal(), renderView()])` instead of sequential calls
- Both independently catch their own errors
- View renders even if sidebar fails (and vice versa)

**Files**: `src/nexus_babel/frontend/static/js/app.js`
**Acceptance**: View loads even when sidebar API call fails. Sidebar loads even when view API call fails.

### T-UX-095: Add Jinja2 template partials [P]

Split `shell.html` into partials for maintainability:

- `_header.html`: Brand, API key controls, navigation
- `_sidebar.html`: Ops monitor panel with status, whoami, jobs
- Main shell includes partials via `{% include "partials/_header.html" %}`
- View-specific content remains in the main `<section>` element

**Files**: `src/nexus_babel/frontend/templates/partials/_header.html` (new), `src/nexus_babel/frontend/templates/partials/_sidebar.html` (new), `src/nexus_babel/frontend/templates/shell.html`
**Acceptance**: Page renders identically after splitting. Partials loaded correctly.

---

## Task Dependency Graph

```
Phase 1 (Setup)
  T-UX-001 [P] (static mount)
  T-UX-002 [P] (manual verification)
  T-UX-003 [P] (smoke tests)

Phase 2 (CSS Extraction) -- depends on T-UX-001
  T-UX-010 -> T-UX-011 [P] (fonts after CSS extraction)
  T-UX-010 -> T-UX-012     (breakpoints after CSS extraction)
  T-UX-013 [P]             (accessibility, independent of CSS)

Phase 3 (JS Extraction) -- depends on T-UX-001, T-UX-010
  T-UX-020                 (JS extraction, depends on static mount + CSS extraction)
  T-UX-020 -> T-UX-021     (API enhancements after extraction)
  T-UX-020 -> T-UX-022     (loading indicators after extraction)
  T-UX-023 [P]             (localStorage fix, independent)
  T-UX-024 [P]             (XSS fix, can run alongside extraction)

Phase 4 (Corpus) -- depends on T-UX-020
  T-UX-030                 (filtering, depends on JS extraction)
  T-UX-031                 (document detail, depends on JS extraction)
  T-UX-030 -> T-UX-032     (pagination, depends on filtering)
  T-UX-033                 (seed corpus, depends on JS extraction)

Phase 5 (Hypergraph) -- depends on T-UX-020
  T-UX-040                 (document selector, depends on JS extraction)
  T-UX-040 -> T-UX-041     (graph viz, depends on document selector)
  T-UX-041 -> T-UX-042     (atom filter, depends on graph viz)

Phase 6 (Timeline) -- depends on T-UX-020
  T-UX-050                 (branch selector, depends on JS extraction)
  T-UX-050 -> T-UX-051     (visual timeline, depends on branch selector)
  T-UX-051 -> T-UX-052     (playback, depends on visual timeline)
  T-UX-053                 (comparison UI, depends on T-UX-050)

Phase 7 (Governance) -- depends on T-UX-020
  T-UX-060                 (mode badge, depends on JS extraction)
  T-UX-061                 (filtering, depends on JS extraction)
  T-UX-062                 (evaluation form, depends on JS extraction)
  T-UX-063                 (statistics, depends on T-UX-061)

Phase 8 (Interaction Nodes) -- depends on Phase 4-7
  T-UX-070 (analyze button, depends on T-UX-031 + T-UX-083)
  T-UX-071 (evolve form, depends on T-UX-050 + T-UX-083)
  T-UX-072 (remix form, depends on T-UX-050 + T-UX-083)
  T-UX-073 (provision button, depends on T-UX-033)

Phase 9 (Components) -- can start after Phase 3, used by Phases 4-8
  T-UX-080 [P] (data table)
  T-UX-081 [P] (JSON viewer)
  T-UX-082 [P] (metric card)
  T-UX-083 [P] (modal dialog)

Phase 10 (Cross-Cutting) -- can run in parallel with later phases
  T-UX-090 [P] (CSP headers, after T-UX-020)
  T-UX-091 [P] (cache headers, after T-UX-001)
  T-UX-092 [P] (CI integration, after T-UX-003)
  T-UX-093 [P] (role gating, after T-UX-020)
  T-UX-094 [P] (parallel loading, after T-UX-020)
  T-UX-095 [P] (template partials, independent)
```

**Legend:** `[P]` = parallelizable with other tasks in the same phase. `->` = depends on.

---

## Summary

| Phase | Tasks | Parallel | Scope | Priority |
|-------|-------|----------|-------|----------|
| Phase 1: Setup | 3 | All [P] | Static mount, baseline verification, smoke tests | P1 |
| Phase 2: CSS Extraction | 4 | Partial | Design system extraction, fonts, breakpoints, a11y | P2 |
| Phase 3: JS Extraction | 5 | Partial | Module extraction, API enhancements, security | P2 |
| Phase 4: Corpus | 4 | Partial | Filtering, detail panel, pagination, seeds | P2/P3 |
| Phase 5: Hypergraph | 3 | Sequential | Document selector, graph visualization, filters | P3 |
| Phase 6: Timeline | 4 | Sequential | Branch selector, visual timeline, playback, compare | P3 |
| Phase 7: Governance | 4 | Partial | Mode badge, filtering, evaluation form, stats | P3 |
| Phase 8: Interactions | 4 | Partial | Analyze, evolve, remix, provision triggers | P3 |
| Phase 9: Components | 4 | All [P] | Data table, JSON viewer, metric card, modal | P3 |
| Phase 10: Cross-Cutting | 6 | All [P] | CSP, caching, CI, role gating, parallel load, partials | P2/P3 |
| **Total** | **41** | | | |
