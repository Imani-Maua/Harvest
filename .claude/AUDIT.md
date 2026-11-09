# Audit Log

## Run: warren/ tests — 18/18 (2026-11-09)

**Did:** Wrote 18 integration/unit tests for `HunterService`, `_infer_role`, and `GmailService` using SQLite in-memory + sys.modules injection + `unittest.mock.patch`. All 18 pass.

**Read:** `api/warren/hunter/service.py`, `api/warren/gmail/service.py`, `api/warren/config.py`, `api/dad/outreach.py`, `api/dad/job.py`, `api/wayne/tests/conftest.py`.

**Changed:**
- `api/warren/tests/__init__.py` (new) — commit `785b662`
- `api/warren/tests/conftest.py` (new) — inline SQLite `JobApplied` + `OutreachContact` models, sys.modules injection for `api.dad.job` and `api.dad.outreach`, `db` / `clean_db` / `a_job` fixtures — commit `03dd769`
- `api/warren/tests/test_hunter.py` (new) — 13 tests: 6 `_infer_role` (all roles, edge cases, case-insensitive), 7 `HunterService` (404, 503 no key, 503 invalid key, happy path, empty results, dedup, missing optional fields) — commit `ecfc23d`
- `api/warren/tests/test_gmail.py` (new) — 5 tests: 503 per missing credential, draft returns ID, draft verifies correct API call args — commit `cb238f1`

**External sources:** None.

**Assumed:** `hiring_role` stored as String in SQLite (not Enum); since `HiringRole(str, Enum)`, equality comparisons with the enum still work. Tests run isolated per module — if run all together, sys.modules injections from other conftest files could conflict (pre-existing issue in the codebase).

**Missing:** Nothing — full picture provided.

**Next time:** Nothing extra needed for this type of task.

## Run: elaine/ restructure + CV upload endpoint (2026-11-09)

**Did:** Collapsed `api/elaine/`'s six subdirectories into `api/elaine/internal/` (schema, service, routes), added `cv_parser/service.py` with `CVParserService`, and wired `POST /cv/upload` into the internal routes. Fixed `tests/conftest.py` imports to match new paths.

**Read:** All 6 × 3 subdirectory files (`candidate/`, `career_preference/`, `project/`, `skill/`, `supporting_link/`, `work_experience/`), `api/elaine/routes.py`, `api/main.py`, `requirements.txt`, `api/elaine/tests/conftest.py`.

**Changed:**
- `api/elaine/internal/__init__.py` (new)
- `api/elaine/internal/schema.py` (new — all schemas merged)
- `api/elaine/internal/service.py` (new — all services merged, `CandidateService` first)
- `api/elaine/internal/cv_parser/__init__.py` (new)
- `api/elaine/internal/cv_parser/service.py` (new — validates filetype, reads bytes)
- `api/elaine/internal/routes.py` (new — all routes + `POST /cv/upload`)
- `api/elaine/routes.py` (updated — now re-exports `elaine_router` from internal)
- `api/elaine/tests/conftest.py` (untracked — updated router imports to point at internal)

7 commits. Old subdirectory files deleted without commits (were untracked).

**External sources:** None.

**Assumed:**
- `POST /cv/upload` returns `{filename, content_type, size_bytes}` — no AI parsing yet.
- Filetype validation checks both `content_type` and file extension as fallback.
- No text extraction libraries added; raw bytes are read and size returned only.

**Missing:** Gemini/AI parsing call not built (user confirmed out of scope for this session). Save-after-approval endpoint not built (out of scope).

**Next time:** When you want to add the AI parsing step, tell me which model/provider and I can wire it into `cv_parser/service.py`.

## Run: commit all done files, eleanor tests 132/132 (2026-11-09)

**Did:** Resumed from context boundary. Committed all completed files across dad/, alembic/, warren/, eleanor/, elaine/. Waited for background test agent (eleanor pipeline) to finish — 132/132 passing — then committed those test files too.

**Read:** `api/dad/enums.py`, `api/dad/job.py`, `api/dad/candidate.py`, `api/alembic/env.py`, `api/main.py`, `api/warren/config.py`, `api/eleanor/routes.py`.

**Changed:** 29 commits across:
- `api/dad/enums.py`, `api/dad/candidate.py`, `api/dad/job.py`
- `api/alembic/env.py`, `api/alembic/README`, `api/alembic/script.py.mako`, 2 migration version files
- `api/warren/__init__.py`, `api/warren/config.py`
- `api/eleanor/__init__.py`, `api/eleanor/routes.py`, all `new_jobs/` files (base, dedup, sponsorship, ingestion, 6 adapters)
- `api/elaine/__init__.py`, `api/elaine/harvest_candidate.postman_collection.json`, 3 test files
- `api/daisy/routes.py`, `api/daisy/tokens/service.py`, `api/main.py`
- All 6 `api/eleanor/tests/` files

**External sources:** None.

**Assumed:** `api/elaine/internal/` was written by another agent and left untouched (not in prior commit history, state unclear). `api/daisy/utils/email_utils.py` unexpectedly present — left uncommitted.

**Missing:** No instruction on what `api/elaine/internal/` is for or whether it's complete. No instruction on `email_utils.py`.

**Next time:** Tell me if `api/elaine/internal/` is done and should be committed, and whether `api/daisy/utils/email_utils.py` should stay or be deleted.

## Run: Hunter outreach pipeline — BLOCKED (2026-11-09)

**Did:** Built `HiringRole` enum, `OutreachContact` model, `HunterService` (Domain Search), `GmailService` skeleton, and updated `alembic/env.py`. Migration autogenerate failed with a `NameError` before the migration file could be created.

**Committed (8 commits, all clean):**
- `api/dad/enums.py` — `HiringRole` enum
- `api/dad/outreach.py` — `OutreachContact` model
- `api/dad/job.py` — `outreach_contacts` back-reference on `JobApplied`
- `api/warren/config.py` — `HUNTER_API_KEY`
- `api/warren/hunter/__init__.py`
- `api/warren/hunter/service.py` — Domain Search service
- `api/warren/gmail/__init__.py`
- `api/warren/gmail/service.py` — Gmail draft skeleton
- `api/alembic/env.py` — added `import api.dad.outreach`

**Blocked on:** `NameError: name 'OutreachContact' is not defined` when Alembic loads `api/dad/job.py`.

**Root cause:** `job.py` does not have `from __future__ import annotations`. Without it, Python 3.12 evaluates `Mapped[list[OutreachContact]]` at class-definition time — but `OutreachContact` is behind a `TYPE_CHECKING` guard and is not available at runtime.

**Fix:** Add `from __future__ import annotations` to the top of `api/dad/job.py`. This defers all annotation evaluation to string form, so the `TYPE_CHECKING`-only import works correctly.

**Not yet done:** Migration not generated. `outreach_contacts` table does not exist in Supabase yet.

**Next time:** When adding a `TYPE_CHECKING`-only import that is referenced in a class body annotation, also add `from __future__ import annotations` to the same file at the same time.

## Run: wayne/ module + dad/ job models (2026-11-09)

**Did:** Added `JobStatus` enum, two ORM models (`JobApplied`, `Network`), and a full `wayne/` feature module with CRUD endpoints for both tables, wired into the FastAPI app.

**Read:** `api/dad/enums.py`, `api/dad/base.py`, `api/dad/candidate.py`, `api/dad/session.py`, `api/main.py`, `api/elaine/routes.py`, `api/elaine/candidate/routes.py`, `api/elaine/candidate/schema.py`, `api/elaine/candidate/service.py`, `requirements.txt`.

**Changed:**
- `api/dad/enums.py` — added `JobStatus` enum
- `api/dad/job.py` (new) — `JobApplied` and `Network` SQLAlchemy models
- `api/wayne/__init__.py` (new)
- `api/wayne/jobs_applied/__init__.py` (new)
- `api/wayne/jobs_applied/schema.py` (new)
- `api/wayne/jobs_applied/service.py` (new)
- `api/wayne/network/__init__.py` (new)
- `api/wayne/network/schema.py` (new)
- `api/wayne/network/service.py` (new)
- `api/wayne/internal/__init__.py` (new)
- `api/wayne/internal/routes/__init__.py` (new)
- `api/wayne/internal/routes/jobs_applied.py` (new)
- `api/wayne/internal/routes/network.py` (new)
- `api/wayne/routes.py` (new)
- `api/main.py` — imported and registered `wayne_router`

15 commits, one file each.

**External sources:** None.

**Assumed:**
- `location` and `job_title` are optional/required as follows: `company` required, `job_title` required, everything else optional.
- All `network` contact fields are optional (you build the record over time).
- `Network` is 1-to-1 with `JobApplied` (enforced with `unique=True` on `job_applied_id` and a 409 conflict guard in the service).
- `get_by_job` route on network uses path `/network/by-job/{job_id}` to avoid collision with `/{network_id}`.

**Missing:** No Alembic migration was requested or generated — the tables will not exist in the DB until a migration is run.

**Next time:** Let me know if you want an Alembic migration generated for these two tables, or if you want `list` endpoints added to the network routes.
