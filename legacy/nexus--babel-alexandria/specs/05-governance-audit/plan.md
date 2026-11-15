# Governance & Audit -- Implementation Plan

## Technical Context

| Component | Version / Stack |
|-----------|----------------|
| Language | Python >=3.11 |
| Web framework | FastAPI (uvicorn) |
| ORM | SQLAlchemy 2.0 (`mapped_column` style) |
| Migrations | Alembic (SQLite default, PostgreSQL via docker) |
| Schema validation | Pydantic v2 + `pydantic-settings` |
| Testing | pytest + `FastAPI.TestClient`, isolated SQLite per test via `tmp_path` |
| Auth | API key hash via SHA256, role hierarchy (viewer < operator < researcher < admin) |
| Regex engine | Python `re` stdlib (word-boundary matching, case-insensitive) |
| Settings | `pydantic-settings`, `NEXUS_` prefix, `.env` file |

## Project Structure

Files directly relevant to the governance-audit domain:

```
src/nexus_babel/
  main.py                           # create_app() factory, lifespan handler (seeds policies via ensure_default_policies)
  config.py                         # Settings (raw_mode_enabled, public_blocked_terms, bootstrap keys)
  db.py                             # DBManager wrapper for engine + sessionmaker
  models.py                         # ModePolicy, PolicyDecision, AuditLog, ApiKey
  schemas.py                        # GovernanceEvaluateRequest, GovernanceEvaluateResponse, Mode literal
  api/
    routes.py                       # POST /governance/evaluate, GET /audit/policy-decisions, _enforce_mode()
  services/
    governance.py                   # GovernanceService (ensure_default_policies, evaluate, list_policy_decisions)
    auth.py                         # AuthService (authenticate, role_allows, mode_allows), AuthContext, ROLE_ORDER

tests/
  conftest.py                       # test_settings, client, auth_headers fixtures (4 roles)
  test_mvp.py                       # test_dual_mode_regression, test_role_and_raw_mode_enforcement
  test_wave2.py                     # test_hypergraph_query_and_audit_decisions (audit decisions query)
```

## Data Models

### ModePolicy (ORM: `models.py:144-154`)

Stores per-mode governance policies. One row per mode (UNIQUE constraint). Policy JSON contains the blocked terms list and behavior configuration.

```
mode_policies
  id              INTEGER PK AUTO  -- sequential
  mode            VARCHAR(16) UQ   -- 'PUBLIC' or 'RAW'
  policy          JSON             -- {"blocked_terms": [...], "redaction_style": "...", "hard_block_threshold": N}
  policy_version  INTEGER          -- starts at 1, incremented on update (currently never incremented)
  effective_from  DATETIME(tz) NL  -- policy active from; NULL = always active
  effective_to    DATETIME(tz) NL  -- policy expires at; NULL = never expires
  created_at      DATETIME(tz)
  updated_at      DATETIME(tz)
```

**Policy JSON schema:**
```python
{
    "blocked_terms": ["kill", "self-harm", "hate", "ethnic cleansing", "bioweapon", "how to make a bomb"],
    "redaction_style": "[REDACTED]",     # PUBLIC: "[REDACTED]", RAW: "[FLAGGED]"
    "hard_block_threshold": 1,           # PUBLIC: 1 (block on first), RAW: 999 (never block)
}
```

**State machine:** Policies are currently static (seeded once, never updated via API). Future CRUD would introduce version transitions:
```
v1 (seeded at startup)
  -> v2 (admin updates blocked_terms)
    -> v3 (admin changes threshold)
      -> rollback to v2 (admin reverts)
```

### PolicyDecision (ORM: `models.py:157-168`)

One row per governance evaluation. Immutable once created.

```
policy_decisions
  id              VARCHAR(36) PK   -- uuid4
  mode            VARCHAR(16)      -- normalized mode, indexed
  input_hash      VARCHAR(128)     -- SHA256(candidate_output), indexed
  allow           BOOLEAN          -- final allow/block decision
  policy_hits     JSON             -- ["kill", "hate"] list of matched terms
  redactions      JSON             -- ["kill", "hate"] list of redacted terms (currently mirrors policy_hits)
  decision_trace  JSON             -- full trace dict (see below)
  audit_id        VARCHAR(36)      -- links to audit_logs.id, indexed (not a formal FK)
  created_at      DATETIME(tz)
```

**Decision trace JSON schema:**
```python
{
    "mode": "PUBLIC",
    "policy_version": 1,
    "hard_block_threshold": 1,
    "hits": [
        {
            "term": "kill",
            "start": 24,
            "end": 28,
            "matched_text": "kill",
            "rule": "blocked_terms",
            "mode": "PUBLIC"
        }
    ],
    "mode_rationale": "PUBLIC blocks flagged terms",
    "redaction_style": "[REDACTED]",
    "allow": false
}
```

### AuditLog (ORM: `models.py:193-201`)

Append-only audit trail. One row per auditable action (currently only `"governance.evaluate"`).

```
audit_logs
  id              VARCHAR(36) PK   -- uuid4
  action          VARCHAR(128)     -- 'governance.evaluate', indexed
  mode            VARCHAR(16)      -- governance mode, indexed
  actor           VARCHAR(128)     -- 'system' (hardcoded currently)
  details         JSON             -- action-specific payload (see below)
  created_at      DATETIME(tz)
```

**Details JSON for `governance.evaluate`:**
```python
{
    "input_preview": "This output says we should kill all nuance...",  # first 240 chars
    "policy_hits": ["kill"],
    "policy_version": 1,
    "allow": false,
    "decision_trace": { ... }  # same as PolicyDecision.decision_trace
}
```

### ApiKey (ORM: `models.py:180-190`) -- governance-relevant fields

```
api_keys
  id                VARCHAR(36) PK
  key_hash          VARCHAR(128) UQ  -- SHA256(plaintext_key)
  owner             VARCHAR(128)     -- 'dev-viewer', 'dev-operator', etc.
  role              VARCHAR(32)      -- 'viewer'|'operator'|'researcher'|'admin'
  enabled           BOOLEAN          -- key active flag
  raw_mode_enabled  BOOLEAN          -- per-key RAW mode flag
  created_at        DATETIME(tz)
  last_used_at      DATETIME(tz) NL
```

**Bootstrap key configuration** (`main.py:38-45`):

| Owner | Role | RAW Enabled |
|-------|------|-------------|
| dev-viewer | viewer | False |
| dev-operator | operator | False |
| dev-researcher | researcher | True |
| dev-admin | admin | True |

## API Contracts

### POST /api/v1/governance/evaluate

**Auth**: operator (minimum), plus mode-specific enforcement
**Request** (`GovernanceEvaluateRequest`):
```json
{
  "candidate_output": "This output says we should kill all nuance.",
  "mode": "PUBLIC"
}
```

- `candidate_output`: The text to evaluate against the governance policy. Required, string.
- `mode`: Either `"PUBLIC"` or `"RAW"`. Defaults to `"PUBLIC"`.

**Response 200** (`GovernanceEvaluateResponse`):
```json
{
  "allow": false,
  "policy_hits": ["kill"],
  "redactions": ["kill"],
  "audit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "decision_trace": {
    "mode": "PUBLIC",
    "policy_version": 1,
    "hard_block_threshold": 1,
    "hits": [
      {
        "term": "kill",
        "start": 31,
        "end": 35,
        "matched_text": "kill",
        "rule": "blocked_terms",
        "mode": "PUBLIC"
      }
    ],
    "mode_rationale": "PUBLIC blocks flagged terms",
    "redaction_style": "[REDACTED]",
    "allow": false
  }
}
```

**Response 200 (RAW mode, same input)**:
```json
{
  "allow": true,
  "policy_hits": ["kill"],
  "redactions": ["kill"],
  "audit_id": "f6e5d4c3-b2a1-0987-dcba-654321fedcba",
  "decision_trace": {
    "mode": "RAW",
    "policy_version": 1,
    "hard_block_threshold": 999,
    "hits": [
      {
        "term": "kill",
        "start": 31,
        "end": 35,
        "matched_text": "kill",
        "rule": "blocked_terms",
        "mode": "RAW"
      }
    ],
    "mode_rationale": "RAW allows flagged terms for research review",
    "redaction_style": "[FLAGGED]",
    "allow": true
  }
}
```

**Response 200 (clean text, no hits)**:
```json
{
  "allow": true,
  "policy_hits": [],
  "redactions": [],
  "audit_id": "00112233-4455-6677-8899-aabbccddeeff",
  "decision_trace": {
    "mode": "PUBLIC",
    "policy_version": 1,
    "hard_block_threshold": 1,
    "hits": [],
    "mode_rationale": "PUBLIC blocks flagged terms",
    "redaction_style": "[REDACTED]",
    "allow": true
  }
}
```

**Error cases**:
- 401: Missing or invalid `X-Nexus-API-Key` header
- 403: Insufficient role (viewer) or unauthorized mode access (operator requesting RAW)
- 400: No policy found for the requested mode (ValueError propagated)

### GET /api/v1/audit/policy-decisions

**Auth**: operator (minimum)
**Query params**:
- `limit`: Integer, 1-1000, default 100

**Response 200**:
```json
{
  "decisions": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "mode": "PUBLIC",
      "allow": false,
      "policy_hits": ["kill"],
      "redactions": ["kill"],
      "decision_trace": {
        "mode": "PUBLIC",
        "policy_version": 1,
        "hard_block_threshold": 1,
        "hits": [ ... ],
        "mode_rationale": "PUBLIC blocks flagged terms",
        "redaction_style": "[REDACTED]",
        "allow": false
      },
      "audit_id": "f6e5d4c3-b2a1-0987-dcba-654321fedcba",
      "created_at": "2026-02-23T12:00:00+00:00"
    }
  ]
}
```

**Error cases**:
- 401: Missing or invalid API key
- 403: Insufficient role (viewer cannot access)

### GET /api/v1/auth/whoami (governance-relevant)

**Auth**: viewer (minimum)
**Response 200**:
```json
{
  "api_key_id": "uuid",
  "owner": "dev-researcher",
  "role": "researcher",
  "raw_mode_enabled": true,
  "allowed_modes": ["PUBLIC", "RAW"]
}
```

The `allowed_modes` list is computed by calling `mode_allows()` for each mode (`routes.py:436-449`). An operator with `raw_mode_enabled=False` would see only `["PUBLIC"]`.

## Service Architecture

### GovernanceService (`governance.py`)

Stateless service class. No constructor parameters. All methods receive a SQLAlchemy `Session`.

**`ensure_default_policies(session, blocked_terms)` flow:**
```
1. Normalize terms: lowercase, strip, deduplicate, sort
2. Build defaults dict:
   - PUBLIC: {blocked_terms, redaction_style="[REDACTED]", hard_block_threshold=1}
   - RAW: {blocked_terms, redaction_style="[FLAGGED]", hard_block_threshold=999}
3. FOR each mode:
   a. Query ModePolicy by mode
   b. IF exists: backfill effective_from if null; SKIP
   c. IF not exists: INSERT new ModePolicy(mode, policy, version=1, effective_from=utcnow())
```

**`evaluate(session, candidate_output, mode)` flow:**
```
1. Normalize mode to uppercase
2. Load ModePolicy with effective date range filter:
   - effective_from IS NULL OR <= utcnow()
   - effective_to IS NULL OR > utcnow()
3. IF no policy: raise ValueError
4. Extract blocked_terms, redaction_style, hard_block_threshold from policy JSON
5. FOR each blocked term:
   a. Skip empty terms
   b. Run re.finditer(r"\b{escaped_term}\b", text, IGNORECASE)
   c. IF matches found:
      - Add term to policy_hits list
      - Add term to redactions list
      - For each match: record {term, start, end, matched_text, rule, mode} in trace hits
      - Apply re.sub to redacted_text with redaction_style
6. Compute allow: len(policy_hits) < hard_block_threshold
7. Build decision_trace dict
8. Create AuditLog record (flush to get ID)
9. Create PolicyDecision record (links to audit via audit_id)
10. Return dict with allow, policy_hits, redactions, audit_id, redacted_text, decision_trace
```

**`list_policy_decisions(session, limit)` flow:**
```
1. Query PolicyDecision ordered by created_at DESC, limit N
2. Return list of dicts with: id, mode, allow, policy_hits, redactions, decision_trace, audit_id, created_at
```

### AuthService (`auth.py`) -- mode_allows()

Determines whether a given role+key combination can access a specific governance mode.

**`mode_allows(current_role, mode, raw_mode_enabled, key_raw_mode_enabled)` flow:**
```
1. Normalize mode to uppercase
2. IF mode == "RAW":
   a. IF global raw_mode_enabled is False -> return False
   b. IF key raw_mode_enabled is False -> return False
   c. Return role_allows(current_role, "researcher")
3. IF mode == "PUBLIC":
   a. Return role_allows(current_role, "operator")
4. ELSE: return False (unknown mode)
```

**`role_allows(current_role, min_role)` flow:**
```
1. ROLE_ORDER = {viewer: 1, operator: 2, researcher: 3, admin: 4}
2. Return ROLE_ORDER[current_role] >= ROLE_ORDER[min_role]
```

### Route Layer (`routes.py`) -- governance endpoints

**`_enforce_mode(request, ctx, mode)` helper:**
```
1. Call auth_service.mode_allows(ctx.role, mode, settings.raw_mode_enabled, ctx.raw_mode_enabled)
2. IF not allowed: raise HTTPException(403)
```

**`governance_evaluate` handler (`routes.py:335-364`):**
```
1. Depends on _require_auth("operator") -> AuthContext
2. Open session
3. Call _enforce_mode(request, auth_context, payload.mode)
4. Call governance_service.evaluate(session, candidate_output, mode)
5. Commit session
6. Return GovernanceEvaluateResponse (maps dict fields to schema; NOTE: redacted_text is dropped)
7. On HTTPException: rollback and reraise
8. On other Exception: rollback, raise 400
9. Finally: close session
```

**`audit_policy_decisions` handler (`routes.py:629-635`):**
```
1. Depends on _require_auth("operator")
2. Open session
3. Call governance_service.list_policy_decisions(session, limit)
4. Return {"decisions": [...]}
5. Finally: close session
```

### Cross-Domain Integration Points

The `_enforce_mode()` helper is called by multiple routes beyond governance:
- `POST /api/v1/analyze` (`routes.py:145`) -- enforces mode for analysis runs
- `POST /api/v1/evolve/branch` (`routes.py:240`) -- enforces mode for evolution
- `POST /api/v1/remix` (`routes.py:691`) -- enforces mode for remix
- `POST /api/v1/jobs/submit` (`routes.py:462-463`) -- enforces mode for analyze jobs

This means mode enforcement is consistently applied across all domain endpoints, but governance _evaluation_ (content filtering) is only available as a standalone API call.

## Research Notes

### Dependencies

| Dependency | Used For | Required? |
|------------|----------|-----------|
| `re` (stdlib) | Word-boundary regex matching for blocked terms | Yes |
| `hashlib` (stdlib) | SHA256 of candidate text for input_hash | Yes |
| `sqlalchemy` | ORM for ModePolicy, PolicyDecision, AuditLog | Yes |
| `pydantic` | Request/response schema validation | Yes |
| `pydantic-settings` | Settings management (raw_mode_enabled, public_blocked_terms) | Yes |

No external dependencies required beyond the core stack.

### Complexity / Performance Considerations

- **Regex compilation**: Each `evaluate()` call compiles regex patterns for every blocked term via `re.finditer()`. For the default 6 terms, this is negligible. If the blocked terms list grows to hundreds, consider pre-compiling patterns at policy load time or combining terms into a single alternation pattern: `\b(kill|hate|...)\b`.
- **Term iteration order**: Terms are iterated in the order they appear in the policy's `blocked_terms` list (sorted alphabetically after `ensure_default_policies`). The `re.sub` for redaction runs per-term sequentially, so earlier term replacements can affect the text seen by later terms. For the current non-overlapping terms this is not an issue, but overlapping terms (e.g., "harm" and "self-harm") could produce unexpected results depending on iteration order.
- **Audit log volume**: Every evaluation creates 2 database rows (AuditLog + PolicyDecision). High-frequency evaluation (e.g., automated pipeline integration) could produce significant audit table growth. Consider partitioning or archival for production.
- **Input preview truncation**: The audit log stores only the first 240 characters of the input. For long texts, this may be insufficient for debugging. The full text is not stored anywhere in the audit trail (only its SHA256 hash in PolicyDecision.input_hash).
- **Session flush for audit_id**: The `session.flush()` after creating the AuditLog (`governance.py:116`) forces a database write to obtain the auto-generated UUID. This happens before `session.commit()`, so both the AuditLog and PolicyDecision are committed atomically. If the commit fails, both are rolled back.

### Known Risks

1. **redacted_text silently dropped**: The `GovernanceEvaluateResponse` schema lacks the `redacted_text` field, so the computed redacted text is returned by the service but never reaches the API consumer. This is a functional gap that could confuse integrators who expect to see the redacted output.
2. **Actor always "system"**: The audit log does not record which API key owner triggered the evaluation. The `auth_context.owner` is available in the route handler but not passed to `GovernanceService.evaluate()`. This reduces audit trail usefulness.
3. **No policy CRUD**: Policies cannot be modified after startup. If a new blocked term needs to be added, the application must be restarted with updated `NEXUS_PUBLIC_BLOCKED_TERMS`. Even then, `ensure_default_policies()` skips existing policies, so the only way to update terms is to delete the ModePolicy rows and restart.
4. **No governance on pipeline outputs**: Evolution and remix can generate text containing blocked terms (e.g., natural drift might surface historic slurs from seed texts), but these outputs bypass governance evaluation entirely. A researcher could receive unfiltered content from `POST /api/v1/evolve/branch` even in PUBLIC mode.
5. **Audit log deduplication**: There is no mechanism to detect or deduplicate repeated evaluations of identical text. The `input_hash` index exists on PolicyDecision but is not used for lookup. High-frequency repeated evaluations (e.g., CI pipelines) could create many duplicate records.
6. **Effective date range untested**: The date range filter in `evaluate()` (`governance.py:48-53`) is implemented but never exercised because policies are created with `effective_from=utcnow()` and `effective_to=None`. Policy expiration logic is unverified.
7. **Regex escaping**: `re.escape(term)` is used correctly (`governance.py:70`), but multi-word terms like "how to make a bomb" will only match if those exact words appear with single spaces. Variations like extra spaces or newlines between words will not match.

### Future Architecture Considerations

- **Policy CRUD API** (US-016): Should be a set of admin-only endpoints: `POST /api/v1/governance/policies`, `PUT /api/v1/governance/policies/{mode}`, `GET /api/v1/governance/policies`. Updates should increment `policy_version` and set `effective_from` on the new version while setting `effective_to` on the old version. Consider storing policy history as separate rows keyed by `(mode, policy_version)` rather than using a single-row-per-mode model.
- **Pipeline governance hooks** (US-014): Should be implemented as a post-processing decorator or middleware that runs `GovernanceService.evaluate()` on service output text before returning. Each pipeline endpoint would opt into governance via a decorator: `@govern_output(mode_from="request")`. The hook should be configurable (enabled/disabled per pipeline via settings).
- **Audit log generalization** (FR-034): The current `AuditLog` model is flexible enough to support any action type. Adding audit entries for ingestion, evolution, remix, etc. only requires calling `session.add(AuditLog(action="ingestion.complete", ...))` at the appropriate service layer. Consider a centralized `AuditService` with typed action creators.
- **Actor propagation** (FR-033): Pass `actor: str` as a parameter to `GovernanceService.evaluate()` and use it instead of the hardcoded `"system"`. The route handler has access to `auth_context.owner`. This is a simple change.
- **Decision caching** (US-015): Before creating a new evaluation, query `PolicyDecision` by `(mode, input_hash, policy_version)`. If a matching decision exists and the policy version has not changed, return the cached result. Include a `cache_hit: bool` field in the response. This requires careful handling of policy version changes invalidating cached decisions.
- **Blocked term taxonomy**: As the blocked terms list grows, consider organizing terms into categories (violence, self-harm, hate speech, weapons, etc.) with per-category thresholds and redaction styles. This would require restructuring the `policy` JSON schema.
