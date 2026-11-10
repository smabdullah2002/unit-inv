# Alembic Database Migrations Guide (Windows)

This guide explains how to manage database migrations with Alembic in the **Unit Management Service** specifically on **Windows** using **PowerShell** or **Command Prompt (cmd.exe)**.

---

## 1. Prerequisites & Virtual Environment

Alembic automatically reads your database configuration from `.env` via `app\core\config.py` and model metadata from `app\models`.

Before running any migration commands, activate your virtual environment:

### PowerShell
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell blocks script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`)*

### Command Prompt (cmd.exe)
```cmd
.\.venv\Scripts\activate.bat
```

> [!TIP]
> You can also run commands directly without activating the virtual environment by prefixing with:
> `.\.venv\Scripts\alembic.exe <command>`

---

## 2. Standard Workflow: After Modifying Models

Follow these 4 steps every time you add, modify, or delete a model in `app\models\`:

### Step 1: Generate a Migration File

Run `alembic revision --autogenerate` with a descriptive message:

```powershell
alembic revision --autogenerate -m "add_column_to_units"
```
*(Or without activating venv: `.\.venv\Scripts\alembic.exe revision --autogenerate -m "add_column_to_units"`)*

Alembic compares your SQLAlchemy models against the database schema and creates a new migration file inside:
```
E:\unit\migrations\versions\<revision_id>_add_column_to_units.py
```

---

### Step 2: Review the Generated Migration File

> [!IMPORTANT]
> **Always inspect the generated file in your editor before applying it.**

Open the generated file in `migrations\versions\` and check:
1. **`upgrade()` function**: Make sure it only includes changes you intended.
2. **`downgrade()` function**: Make sure it reverses the `upgrade()` changes.
3. **Partial Indexes & Enums**: Ensure PostgreSQL/SQLite specific index expressions (e.g., `postgresql_where=sa.text('deleted_at IS NULL')`) were generated correctly.

---

### Step 3: Apply the Migration

Apply the pending migrations to bring your database to the latest schema:

```powershell
alembic upgrade head
```

You will see output showing the migration was applied:
```text
INFO  [alembic.runtime.migration] Running upgrade <old_rev> -> <new_rev>, add_column_to_units
```

---

### Step 4: Verify Migration Status

Verify that your database is now pointing to `head`:

```powershell
alembic current
```

To see the history of applied and pending migrations:
```powershell
alembic history --verbose
```

---

## 3. Rollbacks & Undoing Migrations

If you need to undo a migration:

### Revert the Most Recent Migration (1 step back)
```powershell
alembic downgrade -1
```

### Revert to a Specific Revision ID
```powershell
alembic downgrade <revision_id>
```

### Revert All Migrations (Empty DB Schema)
```powershell
alembic downgrade base
```

---

## 4. Handling Common Migration Scenarios

### Scenario A: Team Branching / Merge Conflicts
When two team members or git branches both create a new migration from the same base revision, Alembic will report:
```text
FAILED: Multiple heads are present; please use the 'alembic merge' command
```

**Solution:**
Create a merge revision combining the heads:
```powershell
alembic merge -m "merge_conflicting_heads" <rev1> <rev2>
alembic upgrade head
```

---

### Scenario B: Database Out of Sync (Stamp)
If your database schema was altered manually or already matches a target migration state, you can record that revision in the `alembic_version` table without running SQL statements:

```powershell
alembic stamp head
# or stamp a specific revision:
alembic stamp <revision_id>
```

---

### Scenario C: Generating a Blank Migration (Manual SQL / Data Backfill)
To create an empty migration script for custom SQL or data operations:

```powershell
alembic revision -m "custom_data_backfill"
```
Then edit the empty `upgrade()` and `downgrade()` functions manually in the newly generated file.

---

## 5. Running the Service on Windows

Once your migrations are up to date, start the FastAPI development server:

```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```
Interactive API docs will be available at: `http://127.0.0.1:8000/docs`

---

## 6. Quick Reference Cheat Sheet (Windows PowerShell)

| Task | PowerShell Command |
|---|---|
| Activate virtual environment | `.\.venv\Scripts\Activate.ps1` |
| Create new migration from models | `alembic revision --autogenerate -m "message"` |
| Create empty migration script | `alembic revision -m "message"` |
| Apply all pending migrations | `alembic upgrade head` |
| Apply next 1 migration | `alembic upgrade +1` |
| Rollback 1 migration | `alembic downgrade -1` |
| Rollback all migrations | `alembic downgrade base` |
| Check current revision in DB | `alembic current` |
| View revision history | `alembic history` |
| Merge conflicting heads | `alembic merge -m "merge" <rev1> <rev2>` |
| Stamp DB without running SQL | `alembic stamp head` |
| Start FastAPI server | `.\.venv\Scripts\uvicorn.exe app.main:app --reload` |

