# Unit Management Service: Plan

A FastAPI service where users manage **units** (kg, litre, piece, etc.). Every unit belongs to a **branch**, and branches are isolated from each other (multitenancy).

## 1. Stack

- Python 3.12, FastAPI, Pydantic v2
- SQLAlchemy 2.0 (async) + asyncpg, PostgreSQL
- Alembic for migrations
- pytest + httpx (AsyncClient) for tests

## 2. Architecture

```
Request
  -> Controller (router)        HTTP only: routes, status codes, DI
  -> Validation (Pydantic)      shape, types, normalization
  -> Service                    business rules, orchestration
  -> Repositories               Unit repo + Branch repo (all SQL lives here)
  -> DB (PostgreSQL)
```

Rules for each layer:

| Layer | Does | Does NOT |
|---|---|---|
| Controller | Parse request, call service, return response model | Touch the DB, hold business logic |
| Validation | Field types, lengths, enums, normalizing codes to lowercase | Check the DB (uniqueness etc.) |
| Service | Branch exists/active, duplicate check, not-found errors, transactions | Build SQL, know about HTTP |
| Repository | Queries, always scoped by `branch_id` | Raise HTTP errors |
| DB | Constraints as the last line of defense | n/a |

## 3. Project structure

```
app/
  main.py
  core/
    config.py            # settings (env)
    database.py          # async engine, session factory, get_session
    exceptions.py        # NotFoundError, ConflictError, ForbiddenError
    error_handlers.py    # exception -> JSON response
  api/
    deps.py              # get_current_user, get_branch_context, get_service
    v1/
      router.py
      units.py           # controller
  schemas/
    unit.py              # UnitCreate, UnitUpdate, UnitOut, UnitListQuery, Page[T]
    common.py            # Page, pagination params
  services/
    unit_service.py
  repositories/
    base.py
    unit_repository.py
    branch_repository.py
  models/
    base.py
    branch.py
    unit.py
migrations/
tests/
  unit/                  # service tests with fake repos
  integration/           # API tests against a test DB
plan.md
```

## 4. Data model

### `branches` (assumed to exist, or minimal version here)

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | text | |
| is_active | bool | default true |

### `units`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| branch_id | UUID FK -> branches.id | NOT NULL, indexed |
| name | varchar(50) | e.g. "Kilogram" |
| code | varchar(10) | e.g. "kg", "l", "pc" (stored lowercase) |
| type | enum | `weight`, `volume`, `count` (extend later) |
| is_active | bool | default true |
| created_at / updated_at | timestamptz | |
| deleted_at | timestamptz null | soft delete |

Constraints and indexes:

- Unique `(branch_id, code)` where `deleted_at IS NULL` (partial unique index)
- Unique `(branch_id, name)` where `deleted_at IS NULL`
- Index `(branch_id, type)` for filtered lists

## 5. Multitenancy (branch isolation)

**Approach: shared schema, `branch_id` column on every tenant table.**

1. The branch comes from the authenticated user's context, **never from the request body**. Two options, pick one:
   - JWT claim `branch_id` (simplest and safest), or
   - `X-Branch-ID` header, validated against the branches the user is allowed to access.
2. A dependency `get_branch_context()` resolves the branch and returns a `BranchContext(branch_id, user_id)`.
3. The service passes `branch_id` into every repository call.
4. The repository **always** adds `WHERE branch_id = :branch_id`. There is no repository method that fetches units without a branch filter.
5. Cross-branch access returns **404** (not 403), so IDs from other branches are not leaked.
6. Optional hardening later: PostgreSQL Row Level Security with `SET LOCAL app.branch_id` per request.

## 6. API design

Base path: `/api/v1/units`

| # | Method | Path | Purpose | Success |
|---|---|---|---|---|
| 1 | POST | `/api/v1/units` | Create unit | 201 + UnitOut |
| 2 | GET | `/api/v1/units/{unit_id}` | Get by id | 200 + UnitOut |
| 3 | GET | `/api/v1/units` | List with filters + pagination | 200 + Page[UnitOut] |
| 4 | PATCH | `/api/v1/units/{unit_id}` | Update (partial) | 200 + UnitOut |
| 5 | DELETE | `/api/v1/units/{unit_id}` | Soft delete (completes CRUD) | 204 |

### Create: request

```json
{ "name": "Kilogram", "code": "kg", "type": "weight" }
```

`branch_id` is taken from the auth context, not the body.

### List: query params

| Param | Type | Default | Notes |
|---|---|---|---|
| `type` | enum | none | filter by weight / volume / count |
| `is_active` | bool | none | |
| `search` | str | none | match on name or code |
| `branch_id` | UUID | user's branch | only honored for users allowed to view multiple branches; otherwise ignored/403 |
| `page` | int >= 1 | 1 | |
| `page_size` | int 1..100 | 20 | |
| `sort_by` | str | `name` | whitelist: name, code, created_at |
| `order` | asc/desc | asc | |

### List: response

```json
{
  "items": [ { "id": "...", "name": "Kilogram", "code": "kg", "type": "weight", "branch_id": "...", "is_active": true } ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

### Error format (consistent)

```json
{ "error": { "code": "UNIT_CODE_EXISTS", "message": "A unit with code 'kg' already exists in this branch." } }
```

| Case | Status |
|---|---|
| Validation error | 422 |
| Unit not found (or other branch) | 404 |
| Duplicate name/code in branch | 409 |
| Branch inactive / not allowed | 403 |
| Unauthenticated | 401 |

## 7. Flow per process

### Create
1. Controller receives `UnitCreate`; Pydantic validates and normalizes (trim name, lowercase code).
2. Service checks the branch exists and is active (BranchRepository).
3. Service checks duplicate `(branch_id, code)` and `(branch_id, name)` (UnitRepository).
4. Repository inserts; DB unique index catches races (map `IntegrityError` -> 409).
5. Return 201.

### Get by id
1. Controller passes `unit_id` + branch context.
2. Service calls `unit_repo.get_by_id(branch_id, unit_id)`.
3. Not found -> 404.

### List
1. Controller builds `UnitListQuery` (filters + pagination) via `Depends()`.
2. Service resolves effective `branch_id`, then calls `unit_repo.list(branch_id, filters, page, page_size, sort)`.
3. Repository runs a count query and a paged query, both with the same filters.

### Update
1. Controller receives `UnitUpdate` (all fields optional, at least one required).
2. Service loads the unit (branch-scoped), 404 if missing.
3. If `name` or `code` changed, re-check duplicates (excluding itself).
4. Repository updates and sets `updated_at`.

### Delete (soft)
1. Load unit (branch-scoped), set `deleted_at`.
2. Later: block delete if the unit is referenced by products (409).

## 8. Implementation steps

1. **Setup**: project skeleton, config, async DB session, Alembic init.
2. **Models + migration**: `branches`, `units`, enums, indexes, partial unique constraints.
3. **Schemas**: `UnitCreate`, `UnitUpdate`, `UnitOut`, `UnitListQuery`, `Page[T]`.
4. **Repositories**: `BranchRepository` (get, is_active), `UnitRepository` (create, get_by_id, list, update, soft_delete, exists_by_code/name).
5. **Service**: `UnitService` with all business rules and exceptions.
6. **Auth + branch context**: `get_current_user`, `get_branch_context` dependencies.
7. **Controller**: routes under `/api/v1/units`, wire dependencies.
8. **Error handling**: global exception handlers, consistent error body.
9. **Tests**: see below.
10. **Polish**: OpenAPI examples, logging with request id, seed data (kg, litre, piece), Dockerfile.

## 9. Testing plan

- **Service unit tests** (fake repositories): duplicate detection, inactive branch, not found, update rules.
- **Repository tests** (real Postgres): branch filter always applied, pagination counts, soft-delete exclusion, partial unique index.
- **API tests**: every endpoint happy path + 404/409/422.
- **Multitenancy tests** (most important): user from branch A cannot read, list, update, or delete branch B's units; same `code` is allowed in two different branches.

## 10. Decisions to confirm

- [ ] Where does the branch come from: JWT claim or `X-Branch-ID` header?
- [ ] Can admins list units across branches, or is it strictly one branch at a time?
- [ ] Is `type` a fixed enum or a user-managed table?
- [ ] Should delete be soft or hard? (Plan assumes soft.)
- [ ] Is there a unit-conversion requirement (1 kg = 1000 g)? Out of scope for v1.
