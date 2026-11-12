# ChronoArb API local setup (Windows PowerShell)

The local default database is SQLite at
`<repository-root>\chronoarb.db`. The configured URL may stay relative
(`sqlite+aiosqlite:///chronoarb.db`); the API resolves it from the repository
root, independent of the working directory. Settings load `.env` from the
repository root as well.

## Install, initialize, seed, and run

Run these commands from the repository root. Python 3.13 or newer is required.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .\packages\domain-python
python -m pip install -e ".\apps\api[dev]"

# The dev-token endpoint needs a local-only signing secret (32 random bytes).
$secretBytes = New-Object byte[] 32
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($secretBytes)
$rng.Dispose()
$env:CHRONOARB_DEV_JWT_SECRET = [Convert]::ToBase64String($secretBytes)

Set-Location .\apps\api
python -m apps.api.init_local_db
python -m apps.api.seed
python -m uvicorn apps.api.main:app --reload
```

`init_local_db` creates missing ORM tables only when the environment is local or
test, auth mode is `dev`, and the configured database is SQLite. The API also
performs this idempotent initialization at startup in that same configuration.
The seed command creates the demo organizations, users, and memberships (along
with the rest of the demo data) and can be run repeatedly.

To keep the local configuration across PowerShell sessions, copy
`.env.example` to `.env` in the repository root and set
`CHRONOARB_DEV_JWT_SECRET` to a random value of at least 32 bytes. Do not use
development authentication in staging or production.

## Alembic / PostgreSQL

Alembic revision `a40b5bfef9a2` defines `organizations`, `users`, and
`memberships`. The current migrations use PostgreSQL-specific types and are not
the schema setup path for the default SQLite development database. For a
PostgreSQL database, run the Alembic command from `apps\api`:

```powershell
python -m alembic -c ..\..\alembic.ini upgrade heads
```

`heads` is used because the repository currently has multiple migration heads.
The two branches both create `stripe_webhook_events`; reconcile that existing
migration conflict before applying all PostgreSQL heads to a database.

## Verify the development token

With the server running, use a second PowerShell window:

```powershell
$body = @{ email = "dealer@demo.example.com" } | ConvertTo-Json
$response = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/api/v1/identity/dev-token" `
    -ContentType "application/json" `
    -Body $body

$response.data | Select-Object user_id, email, organization_id, role
$response.data.access_token
```

The response should contain the seeded dealer, the `demo` organization, role
`dealer`, and an access token.
