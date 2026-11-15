# Explorer UX -- Implementation Plan

## Technical Context

### Current State

| Component | Technology | Status |
|-----------|-----------|--------|
| Template Engine | Jinja2 (FastAPI built-in) | Implemented |
| CSS | Inline `<style>` in shell.html | Implemented |
| JavaScript | Inline `<script>` in shell.html, vanilla JS | Implemented |
| Font Stack | IBM Plex Sans/Mono (declared, not loaded) | Declared only |
| Static Assets | None (no mount, no directory) | Not implemented |
| Framework | None (no JS framework) | Not implemented |
| Build Tool | None (no bundler, no transpiler) | Not implemented |
| Test Runner | None (no frontend tests) | Not implemented |

### Backend Stack (consumed by frontend)

| Component | Technology | Version |
|-----------|-----------|---------|
| API Framework | FastAPI | latest |
| Authentication | API key via `X-Nexus-API-Key` header | Implemented |
| Response Format | JSON | All endpoints |
| CORS | Not configured (same-origin assumed) | N/A |

### Frontend Stack Decision: Minimal vs Full Framework

The frontend must balance three concerns: (1) the project is currently an internal alpha with a single-file frontend, (2) the vision requires interactive visualizations and component reuse, and (3) the system runs as a Python-first monolith where frontend complexity should be proportional to the application's needs.

**Option A: Progressive Enhancement (Recommended for P2)**

Keep the Jinja2 shell, extract CSS/JS to static files, add Alpine.js or htmx for interactivity, and bring in visualization libraries (D3.js, vis.js) as needed. No build step required.

- Pros: Zero build tooling, works with existing template, incremental adoption, small bundle size
- Cons: No type checking, no component testing framework, manual DOM management for complex UIs
- Best for: Internal tools, small teams, Python-centric projects

**Option B: Lightweight SPA (Recommended for P3)**

Replace shell.html with a Preact or Lit-based SPA served from `/static/`. Use Vite for development and bundling. The FastAPI backend serves the SPA at `/app/*` via a catch-all route.

- Pros: Component model, type safety (with TS), HMR during development, testable components
- Cons: Build step required, additional tooling complexity, larger initial investment
- Best for: Projects that will grow beyond 5 views or need complex state management

**Option C: Full React/Vue SPA (P3+ only if needed)**

Full framework with routing, state management (Zustand, Pinia), and component library.

- Pros: Mature ecosystem, extensive libraries, strong community support
- Cons: Heavy tooling, large bundle, overkill for 4 views, decouples from Python deployment
- Best for: Projects with dedicated frontend engineers, >10 views, complex client-side state

**Recommendation:** Start with **Option A** for P2 (static file extraction, Alpine.js for interactivity, D3/vis.js for visualizations). Evaluate migrating to **Option B** if the frontend grows beyond 6 views or requires client-side routing.

---

## Project Structure

### Current Structure

```
src/nexus_babel/
  main.py                                  # app_view route, Jinja2Templates setup
  frontend/
    templates/
      shell.html                           # Single-file: HTML + CSS + JS (357 lines)
```

### Target Structure (P2: Static Extraction)

```
src/nexus_babel/
  main.py                                  # Add: app.mount("/static", ...)
  frontend/
    templates/
      shell.html                           # Slimmed: HTML structure only, references external CSS/JS
      partials/                            # Jinja2 includes for reusable blocks
        _header.html                       # Brand + API key + nav
        _sidebar.html                      # Ops monitor panel
        _corpus.html                       # Corpus view skeleton
        _hypergraph.html                   # Hypergraph view skeleton
        _timeline.html                     # Timeline view skeleton
        _governance.html                   # Governance view skeleton
    static/
      css/
        design-system.css                  # Custom properties, reset, typography, grid
        components.css                     # .panel, .metric, .row, .list, buttons
        views/
          corpus.css                       # Corpus-specific styles
          hypergraph.css                   # Graph visualization styles
          timeline.css                     # Timeline visualization styles
          governance.css                   # Governance dashboard styles
      js/
        api.js                             # api() helper, auth key management, error handling
        app.js                             # Boot logic, view router, loadGlobal()
        views/
          corpus.js                        # renderCorpus(), document detail
          hypergraph.js                    # renderHypergraph(), graph visualization
          timeline.js                      # renderTimeline(), event playback
          governance.js                    # renderGovernance(), filtering
        components/
          data-table.js                    # Reusable sortable/filterable table
          metric-card.js                   # Metric display card
          json-viewer.js                   # Collapsible JSON viewer
          modal.js                         # Modal dialog
          loading.js                       # Loading spinner/skeleton
      fonts/
        ibm-plex-sans-*.woff2             # Self-hosted IBM Plex Sans
        ibm-plex-mono-*.woff2             # Self-hosted IBM Plex Mono
      vendor/                              # Third-party libraries (no npm)
        alpine.min.js                      # Alpine.js (optional)
        d3.min.js                          # D3.js for graph visualization
        d3-force.min.js                    # D3 force layout
```

### Target Structure (P3: Lightweight SPA -- if adopted)

```
frontend/                                  # Separate directory at project root
  package.json                             # Preact/Lit + Vite
  vite.config.ts                           # Build config, proxy to FastAPI dev server
  tsconfig.json                            # TypeScript strict mode
  src/
    main.ts                                # SPA entry point
    router.ts                              # Client-side routing
    api.ts                                 # Typed API client
    stores/                                # State management
    components/                            # Shared components
    views/                                 # View components
  tests/                                   # Component tests (Vitest)
  dist/                                    # Build output (served by FastAPI)
```

---

## Data Models

The frontend does not maintain its own data models. It consumes backend API responses and renders them directly. The following documents the API contracts the frontend depends on, with emphasis on the response shapes.

### Authentication Context

**Endpoint:** `GET /api/v1/auth/whoami`
**Auth:** viewer (minimum)

```typescript
// Response shape
interface WhoamiResponse {
  api_key_id: string;       // UUID
  owner: string;            // e.g., "dev-operator"
  role: string;             // "viewer" | "operator" | "researcher" | "admin"
  raw_mode_enabled: boolean;
  allowed_modes: string[];  // ["PUBLIC"] or ["PUBLIC", "RAW"]
}
```

**Frontend usage:** Sidebar identity display, role-gated UI elements (P3).

### Health Status

**Endpoint:** `GET /healthz`
**Auth:** none

```typescript
interface HealthResponse {
  status: string;  // "ok"
}
```

**Frontend usage:** Sidebar health indicator.

### Document List

**Endpoint:** `GET /api/v1/documents`
**Auth:** viewer

```typescript
interface DocumentListResponse {
  documents: Array<{
    id: string;                        // UUID
    path: string;                      // Absolute file path
    modality: string;                  // "text" | "pdf" | "image" | "audio" | "binary"
    ingested: boolean;
    ingest_status: string;             // "pending" | "parsed" | "ingested" | "unchanged" | "conflict" | "ingested_with_warnings"
    conflict_flag: boolean;
    conflict_reason: string | null;
    atom_count: number;
    graph_projected_atom_count: number;
    graph_projection_status: string;   // "pending" | "complete" | "partial" | "failed"
    modality_status: Record<string, string>;
    provider_summary: Record<string, string>;
  }>;
}
```

**Frontend usage:** Corpus view document listing and metrics.

### Document Detail

**Endpoint:** `GET /api/v1/documents/{id}`
**Auth:** viewer

```typescript
interface DocumentDetailResponse {
  id: string;
  path: string;
  title: string;                       // Filename
  modality: string;
  ingested: boolean;
  ingest_status: string;
  conflict_flag: boolean;
  conflict_reason: string | null;
  atom_count: number;
  graph_projected_atom_count: number;
  graph_projection_status: string;
  modality_status: Record<string, string>;
  provider_summary: Record<string, string>;
  provenance: {
    extracted_text?: string;
    segments?: Record<string, any>;
    checksum?: string;
    raw_storage_path?: string;
    cross_modal_links?: Array<{
      target_document_id: string;
      target_modality: string;
      anchors: Record<string, any>;
    }>;
    hypergraph?: Record<string, any>;
  } | null;
}
```

**Frontend usage:** Document detail panel (P3).

### Branch List

**Endpoint:** `GET /api/v1/branches?limit={n}`
**Auth:** viewer

```typescript
interface BranchListResponse {
  branches: Array<{
    id: string;                     // UUID
    parent_branch_id: string | null;
    root_document_id: string | null;
    mode: string;                   // "PUBLIC" | "RAW"
    branch_version: number;
    created_at: string;             // ISO 8601
  }>;
}
```

**Frontend usage:** Timeline view branch listing.

### Branch Timeline

**Endpoint:** `GET /api/v1/branches/{id}/timeline`
**Auth:** viewer

```typescript
interface BranchTimelineResponse {
  branch_id: string;
  root_document_id: string | null;
  events: Array<{
    branch_id: string;
    event_id: string;
    event_index: number;
    event_type: string;             // "natural_drift" | "synthetic_mutation" | "phase_shift" | "glyph_fusion" | "remix"
    event_payload: Record<string, any>;
    diff_summary: Record<string, any>;
    created_at: string;
  }>;
  replay_snapshot: Record<string, any>;
}
```

**Frontend usage:** Timeline event listing and playback (P3).

### Branch Replay

**Endpoint:** `POST /api/v1/branches/{id}/replay`
**Auth:** viewer

```typescript
interface BranchReplayResponse {
  branch_id: string;
  event_count: number;
  text_hash: string;
  preview: string;                  // First N characters of replayed text
  replay_snapshot: Record<string, any>;
}
```

**Frontend usage:** Timeline replay display.

### Branch Compare

**Endpoint:** `GET /api/v1/branches/{id}/compare/{other}`
**Auth:** viewer

```typescript
interface BranchCompareResponse {
  left_branch_id: string;
  right_branch_id: string;
  left_hash: string;
  right_hash: string;
  distance: number;                 // Character-level edit distance
  same: boolean;
  preview_left: string;
  preview_right: string;
}
```

**Frontend usage:** Timeline branch comparison.

### Hypergraph Integrity

**Endpoint:** `GET /api/v1/hypergraph/documents/{id}/integrity`
**Auth:** viewer

```typescript
interface HypergraphIntegrityResponse {
  document_nodes: number;
  atom_nodes: number;
  consistent: boolean;
  // Additional fields vary
}
```

**Frontend usage:** Hypergraph metrics display.

### Hypergraph Query

**Endpoint:** `GET /api/v1/hypergraph/query?document_id={id}&node_id={id}&relationship_type={type}&limit={n}`
**Auth:** viewer

```typescript
interface HypergraphQueryResponse {
  count: { nodes: number; edges: number };
  nodes: Array<{ id: string; type: string; properties: Record<string, any> }>;
  edges: Array<{ source: string; target: string; type: string; properties: Record<string, any> }>;
}
```

**Frontend usage:** Hypergraph neighborhood display, graph visualization (P3).

### Policy Decisions

**Endpoint:** `GET /api/v1/audit/policy-decisions?limit={n}`
**Auth:** operator

```typescript
interface PolicyDecisionListResponse {
  decisions: Array<{
    mode: string;                   // "PUBLIC" | "RAW"
    allow: boolean;
    policy_hits: string[];
    audit_id: string;
    decision_trace: Record<string, any>;
  }>;
}
```

**Frontend usage:** Governance view decision listing.

### Job List

**Endpoint:** `GET /api/v1/jobs?limit={n}`
**Auth:** viewer

```typescript
interface JobListResponse {
  jobs: Array<{
    job_id: string;
    job_type: string;
    status: string;                 // "queued" | "running" | "succeeded" | "failed" | "cancelled" | "retry_wait"
    execution_mode: string;
    attempt_count: number;
    max_attempts: number;
    created_at: string;
    updated_at: string;
  }>;
}
```

**Frontend usage:** Sidebar jobs panel.

### Seed Corpus

**Endpoint:** `GET /api/v1/corpus/seeds`
**Auth:** viewer

```typescript
interface SeedTextListResponse {
  seeds: Array<{
    title: string;
    author: string;
    language: string;
    source_url: string;
    local_path: string | null;
    atomization_status: string;     // "not_provisioned" | "provisioned" | "already_provisioned"
  }>;
}
```

**Frontend usage:** Seed corpus listing (P3).

---

## API Integration Patterns

### Current Pattern (Inline in shell.html)

The `api()` helper function handles all backend communication:

```javascript
async function api(path, options = {}) {
  const apiKey = getApiKey(); // allow-secret
  const headers = { ...(options.headers || {}) };
  if (apiKey) headers["X-Nexus-API-Key"] = apiKey; // allow-secret
  if (!headers["Content-Type"] && options.body) headers["Content-Type"] = "application/json";
  const response = await fetch(path, { ...options, headers });
  const text = await response.text();
  let data = null;
  try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
  if (!response.ok) throw new Error(data.detail || text || `HTTP ${response.status}`);
  return data;
}
```

**Key behaviors:**
- API key injected from localStorage on every request
- Content-Type set to application/json when body is present
- Response parsed as JSON with fallback to `{raw: text}`
- Non-2xx responses throw with the `detail` field from the error response
- No request timeout, no retry, no abort controller

### Target Pattern (P2: Extracted api.js)

```javascript
// api.js -- extracted and enhanced
const API_TIMEOUT_MS = 15000;

class NexusApiClient {
  #keyStore;

  constructor(keyStore) {
    this.#keyStore = keyStore;
  }

  async request(path, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
    try {
      const apiKey = this.#keyStore.get(); // allow-secret
      const headers = { ...(options.headers || {}) };
      if (apiKey) headers["X-Nexus-API-Key"] = apiKey; // allow-secret
      if (!headers["Content-Type"] && options.body) {
        headers["Content-Type"] = "application/json";
      }
      const response = await fetch(path, {
        ...options,
        headers,
        signal: controller.signal,
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(response.status, error.detail || `HTTP ${response.status}`);
      }
      return response.json();
    } finally {
      clearTimeout(timeout);
    }
  }

  // Convenience methods
  get(path) { return this.request(path); }
  post(path, body) { return this.request(path, { method: "POST", body: JSON.stringify(body) }); }
}
```

**Improvements over current:**
- AbortController for request timeouts
- Typed error class (`ApiError`) with status code
- Separated key storage from API client
- Method convenience wrappers

### Error Handling Strategy

| Error Type | Current Behavior | Target Behavior (P2) |
|------------|-----------------|---------------------|
| 401 Unauthorized | Generic "Auth/API unavailable" | Distinct "API key invalid or missing" message with prompt to enter key |
| 403 Forbidden | Same as 401 | "Insufficient permissions: {detail}" with role indicator |
| 404 Not Found | Generic error | Context-specific: "Document not found" vs "Branch not found" |
| 500 Server Error | Generic error | "Server error -- check system health" with link to healthz |
| Network Error | Generic error | "Network unavailable -- check connection" |
| Timeout | None (hangs) | "Request timed out after 15s" |

---

## Wireframes and Layout Descriptions

### Shell Layout (Current, All Views)

```
+---------------------------------------------------------------+
| [Brand: Nexus Babel-Alexandria | Internal Alpha]  [API Key: ****] [Save] [Clear] |
| [Corpus] [Hypergraph] [Timeline] [Governance]                               |
+------------------------------------------+--------------------+
|                                          |                    |
|  {View} Workspace                        |  Ops Monitor       |
|  +------------------------------------+  |  System: healthy   |
|  |                                    |  |  role=operator ... |
|  |  (view-specific content)           |  |                    |
|  |                                    |  |  Recent Jobs:      |
|  |                                    |  |  [job card]        |
|  |                                    |  |  [job card]        |
|  +------------------------------------+  |  [job card]        |
|                                          |                    |
+------------------------------------------+--------------------+

Grid: 1.7fr | 1fr (collapses to 1fr at 980px)
Max width: 1200px, centered
```

### Corpus View Detail (P3 Vision)

```
+------------------------------------------+--------------------+
|  Corpus Workspace                        |  Ops Monitor       |
|                                          |                    |
|  [Metrics: Total | Ingested | Projected] |  ...               |
|  [Conflicts: N]                          |                    |
|                                          |                    |
|  [Search: ________] [Modality: v] [Status: v]                |
|                                          |                    |
|  +------------------------------------+  |                    |
|  | sample.md  text  ingested  complete|  |                    |
|  | odyssey.txt text ingested  complete|  |                    |
|  | image.png  image ingested  n/a    |  |                    |
|  +------------------------------------+  |                    |
|                                          |                    |
|  --- Document Detail (expanded) ---      |                    |
|  Title: sample.md                        |                    |
|  Modality: text | Size: 1.2KB            |                    |
|  Checksum: sha256:abc...                 |                    |
|                                          |                    |
|  Atoms by Level:                         |                    |
|  glyph-seed: 847 | syllable: 203        |                    |
|  word: 156 | sentence: 12 | para: 3     |                    |
|                                          |                    |
|  [Analyze] [Evolve] [Remix]             |                    |
+------------------------------------------+--------------------+
```

### Hypergraph View (P3 Vision)

```
+------------------------------------------+--------------------+
|  Hypergraph Workspace                    |  Ops Monitor       |
|                                          |                    |
|  [Document: v select] [Level: v]         |  ...               |
|  [Nodes: 847] [Edges: 847] [Consistent] |                    |
|                                          |                    |
|  +------------------------------------+  |                    |
|  |                                    |  |                    |
|  |     (D3 force-directed graph)      |  |                    |
|  |                                    |  |                    |
|  |  [doc:abc]--CONTAINS-->[atom:1]    |  |                    |
|  |           \--CONTAINS-->[atom:2]   |  |                    |
|  |                                    |  |                    |
|  |  [zoom +] [zoom -] [reset]        |  |                    |
|  +------------------------------------+  |                    |
|                                          |                    |
|  --- Node Detail (on click) ---          |                    |
|  Type: atom | Level: word                |                    |
|  Content: "Sing"                         |                    |
|  Edges: 1 (CONTAINS from doc:abc)        |                    |
+------------------------------------------+--------------------+
```

### Timeline View (P3 Vision)

```
+------------------------------------------+--------------------+
|  Timeline Workspace                      |  Ops Monitor       |
|                                          |                    |
|  Branch Tree:                            |  ...               |
|  main --+-- branch-1 (natural_drift x3) |                    |
|         +-- branch-2 (synthetic x2)     |                    |
|                                          |                    |
|  --- Branch-1 Timeline ---               |                    |
|  [> play] [|| pause] [<< reset]         |                    |
|                                          |                    |
|  |--[drift]--[drift]--[drift]--|        |                    |
|   e0          e1         e2              |                    |
|                                          |                    |
|  Event e1: natural_drift                 |                    |
|  Shift: great_vowel_shift                |                    |
|  Before: "hous" -> After: "house"        |                    |
|                                          |                    |
|  --- Compare ---                         |                    |
|  [Branch-1] vs [Branch-2 v]             |                    |
|  Distance: 47 chars | Same: no           |                    |
|  Left:  "Sing, O goddess..."            |                    |
|  Right: "S1ng, 0 g0dd3ss..."            |                    |
|                                          |                    |
|  [Evolve Branch] [Remix]                |                    |
+------------------------------------------+--------------------+
```

### Governance View (P3 Vision)

```
+------------------------------------------+--------------------+
|  Governance Workspace                    |  Ops Monitor       |
|                                          |                    |
|  Mode: [PUBLIC]  (user: operator)        |  ...               |
|                                          |                    |
|  Stats: Decisions: 47 | Blocked: 3 (6%) |                    |
|                                          |                    |
|  [Mode: v] [Status: v] [Date: v]        |                    |
|                                          |                    |
|  +------------------------------------+  |                    |
|  | 2026-02-23 PUBLIC ALLOW  hits=none |  |                    |
|  | 2026-02-23 PUBLIC BLOCK  hits=hate |  |                    |
|  | 2026-02-22 RAW    ALLOW  hits=prof |  |                    |
|  +------------------------------------+  |                    |
|                                          |                    |
|  --- Decision Detail ---                 |                    |
|  Audit ID: abc-123                       |                    |
|  Trace: {policy: "hate_speech", ...}     |                    |
|                                          |                    |
|  --- Evaluate Text ---                   |                    |
|  [Text: ___________] [Mode: PUBLIC v]    |                    |
|  [Evaluate]                              |                    |
+------------------------------------------+--------------------+
```

---

## Research Notes

### CSS Framework Decision

The current inline CSS is ~150 lines and covers the full design system. For P2, extracting to external files is sufficient. No CSS framework (Tailwind, Bootstrap) is recommended at this stage:

- **Tailwind CSS:** Would require a build step (PostCSS, JIT compiler). Overkill for 4 views.
- **Bootstrap:** Opinionated styling conflicts with the custom design system (`--ink`, `--paper`, etc.).
- **No framework:** The existing custom properties + utility classes pattern is lightweight and sufficient.

If the frontend grows to 10+ views, consider adopting **Open Props** (CSS custom properties library) for extended tokens.

### Visualization Library Options

| Library | Size | Features | Complexity | Best For |
|---------|------|----------|------------|----------|
| **D3.js** | 80KB min | Full control, force layouts, transitions | High | Custom graph visualization |
| **vis.js Network** | 200KB min | Built-in graph component, physics engine | Low | Quick graph explorer |
| **Cytoscape.js** | 180KB min | Graph analysis algorithms, styles | Medium | Graph-heavy applications |
| **Sigma.js** | 50KB min | WebGL rendering, large graphs | Medium | Performance with 10K+ nodes |

**Recommendation for hypergraph:** Start with **vis.js Network** for P3 (quick setup, built-in zoom/pan/drag). Migrate to **D3.js** if custom rendering is needed. For the timeline, D3 scales/axes are more appropriate than a graph library.

**Recommendation for timeline:** Use **D3.js** for the timeline axis and event positioning. The timeline is a 1D layout (time axis) with branching, which maps well to D3's scale and axis primitives. For simple timeline rendering, a custom SVG with vanilla JS is also viable.

### Alpine.js for Interactivity (P2)

Alpine.js (15KB min) provides reactive data binding without a build step. It can be added via `<script src>` and used with `x-data`, `x-on`, `x-bind` attributes directly in HTML.

**Applicable patterns:**
- Filter dropdowns: `x-data="{modality: 'all', status: 'all'}"` with `x-on:change` handlers
- Document detail toggle: `x-show="selectedDoc === doc.id"`
- Loading states: `x-show="loading"` on skeleton elements
- Modal dialogs: `x-data="{open: false}"` with `x-show` transition

**Note:** Alpine.js is fully optional. The current vanilla JS approach is functional and the added dependency should only be introduced if it simplifies multiple interaction patterns.

### Accessibility Considerations

The current shell has no accessibility features. P2 should address:

1. **ARIA landmarks:** `<header role="banner">`, `<main role="main">`, `<aside role="complementary">`, `<nav role="navigation">`
2. **Skip link:** Hidden link at top of page to skip to main content
3. **Focus management:** When view changes, move focus to the view heading
4. **Color contrast:** Verify `--ink` on `--paper` meets WCAG AA (4.5:1 ratio). Current `#102134` on `#f6f8fb` = 12.2:1 (passes).
5. **Keyboard navigation:** Ensure all interactive elements are reachable via Tab and activatable via Enter/Space
6. **ARIA labels:** All icon-only buttons need `aria-label`. API key input needs associated `<label>`.
7. **Reduced motion:** Respect `prefers-reduced-motion` media query for any animations

### Security Considerations

1. **XSS via innerHTML:** Current implementation uses template literals with `innerHTML` assignment. User-controlled data (document paths, error messages) could contain script tags or event handlers. Mitigation: Use `textContent` for plain text, or sanitize HTML strings.

2. **API key in localStorage:** localStorage is accessible to any JavaScript on the page. If a third-party script is loaded (e.g., from a CDN), it could steal the key. Mitigation: Use `sessionStorage` instead (cleared on tab close), or implement HttpOnly cookie-based session auth.

3. **CSRF:** Not currently a concern since the API uses API key auth (not cookie-based), and the frontend is same-origin. If cookie-based sessions are added, CSRF tokens will be needed.

4. **Content Security Policy:** No CSP headers are set. Adding `Content-Security-Policy: default-src 'self'; script-src 'self'` would prevent inline script execution. This conflicts with the current inline `<script>` approach and must be addressed when extracting to external files.

### Font Loading Strategy

IBM Plex is available on Google Fonts and as self-hosted WOFF2 files. For an internal alpha:

- **Option A (quick):** Google Fonts `<link>` tag in `<head>`. Adds external dependency.
- **Option B (self-hosted):** Download WOFF2 files to `static/fonts/`, add `@font-face` declarations. No external dependency. Slightly larger initial payload.

**Recommendation:** Option B (self-hosted) to avoid external dependencies and ensure offline functionality.

### Performance Budget

For an internal alpha with typically <100 documents, performance is not critical. Baseline targets:

| Metric | Target | Notes |
|--------|--------|-------|
| Initial page load | < 2s on localhost | Shell HTML + inline CSS/JS |
| View switch (navigation) | < 500ms | Full page reload (Jinja2 re-render) |
| API call latency | < 200ms p95 | Backend response time |
| Document list render | < 100ms for 100 docs | DOM insertion via innerHTML |
| Graph visualization (P3) | < 3s for 1000 nodes | Force simulation settle time |

When extracting to static files, add cache headers (`Cache-Control: public, max-age=3600` for CSS/JS, `no-cache` for HTML).

### Test Strategy

**P2: Manual testing + basic smoke tests**
- Browser console should show no errors on page load
- All 4 views render with valid API key
- API key persistence across reload
- Error display on invalid key
- Responsive layout at 980px and below

**P3: Automated tests**
- **Playwright end-to-end:** Navigate to each view, verify content renders, test interactions
- **Component tests (if SPA):** Vitest + Testing Library for component behavior
- **Visual regression:** Screenshot comparison across builds (optional)
- **Accessibility audit:** axe-core integration in Playwright tests

---

## Dependencies on Other Domains

The Explorer UX domain consumes endpoints from every other domain. The following table maps frontend features to backend domain dependencies:

| Frontend Feature | Backend Domain | Endpoints Used | Status |
|-----------------|---------------|----------------|--------|
| Corpus listing | 01-ingestion-atomization | `GET /documents` | Implemented |
| Document detail | 01-ingestion-atomization | `GET /documents/{id}` | Implemented |
| Seed corpus | 01-ingestion-atomization | `GET /corpus/seeds`, `POST /corpus/seed` | Implemented |
| Analysis runs | 02-linguistic-analysis | `GET /analysis/runs`, `GET /analysis/runs/{id}` | Implemented |
| Branch listing | 03-evolution-branching | `GET /branches`, timeline, replay, compare | Implemented |
| Remix trigger | 04-remix-recombination | `POST /remix` | Implemented |
| Governance decisions | 05-governance-audit | `GET /audit/policy-decisions`, `POST /governance/evaluate` | Implemented |
| Hypergraph queries | 07-hypergraph | `GET /hypergraph/query`, integrity | Implemented |
| Auth, jobs, health | 08-platform-infrastructure | `GET /auth/whoami`, `GET /jobs`, `GET /healthz`, `GET /metrics` | Implemented |
| Atom-level queries | 01-ingestion-atomization | Per-atom API endpoint | **Not yet built** |
| Admin key management | 08-platform-infrastructure | Key CRUD endpoints | **Not yet built** |
| Thread/comments | (new domain) | Thread CRUD endpoints | **Not yet built** |
| Document search | 01-ingestion-atomization | Search/filter endpoint | **Not yet built** |

**Implication:** P1 and P2 work can proceed using only existing endpoints. P3 features (atom drill-down, admin panel, threads) require new backend endpoints.
