# Hours24 Backend

FastAPI backend MVP for the AI content asset production system.

## Local Run

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Edit `.env` and set `DATABASE_URL` to your MySQL connection.

Create the MySQL database before starting the backend:

```sql
CREATE DATABASE hours24
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE DATABASE hours24_test
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'hours24'@'%' IDENTIFIED BY 'hours24_password';
GRANT ALL PRIVILEGES ON hours24.* TO 'hours24'@'%';
GRANT ALL PRIVILEGES ON hours24_test.* TO 'hours24'@'%';
FLUSH PRIVILEGES;
```

Initialize tables and default RBAC data:

```powershell
python -m app.db.init_db
```

Start the API:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Default admin account:

- username: `admin`
- password: `admin123456`

API docs: `http://127.0.0.1:8001/docs`

## Database

Runtime uses async SQLAlchemy. The default production-style connection is MySQL:

```text
mysql+asyncmy://hours24:hours24_password@127.0.0.1:3306/hours24?charset=utf8mb4
```

Alembic uses the sync PyMySQL driver internally:

```text
mysql+pymysql://hours24:hours24_password@127.0.0.1:3306/hours24?charset=utf8mb4
```

Tests use MySQL as well. By default they connect to:

```text
mysql+asyncmy://hours24:hours24_password@127.0.0.1:3306/hours24_test?charset=utf8mb4
```

Set `DATABASE_URL` before running tests if your local MySQL account differs.

## Server Deployment Notes

On a server, do not edit source code for environment-specific settings. Put these values in `.env` or system environment variables:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ENCRYPTION_KEY`
- `CORS_ORIGINS`
- `REDIS_URL`
- object storage credentials

Recommended production process:

```powershell
python -m app.db.init_db
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

For Linux servers, run the same command under systemd, Supervisor, Docker, or another process manager, and put Nginx in front for HTTPS and reverse proxying.
