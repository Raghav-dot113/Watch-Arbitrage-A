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

Set-Location .\apps\api
python -m apps.api.init_local_db
python -m apps.api.seed
python -m uvicorn apps.api.main:app --reload
```

`init_local_db` creates missing ORM tables for local SQLite. The API also performs
this idempotent initialization at startup. The seed command creates the demo
organizations, users, and memberships (along with the rest of the demo data) and
can be run repeatedly.

To keep the local configuration across PowerShell sessions, copy
`.env.example` to `.env` in the repository root. The hackathon default is
`CHRONOARB_AUTH_MODE=disabled`: the API uses the seeded
`owner@demo.example.com` user and no login is required. Set
`CHRONOARB_DEMO_USER_EMAIL` to use a different seeded account.

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

## Verify demo mode

With the server running, open:

- Web app: `http://localhost:3000/opportunities`
- API docs: `http://127.0.0.1:8000/docs`

No login screen is shown. Unauthenticated API calls use the seeded demo account:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/opportunities?limit=2"
```

The response contains the demo opportunities. See
[the Render deployment guide](../../docs/deployment/render.md) for the hosted
configuration.

## Telegram alerts

Alert delivery needs a bot token and a destination chat. Set these in the
repository-root `.env`:

```dotenv
CHRONOARB_TELEGRAM_BOT_TOKEN=<token from @BotFather>
CHRONOARB_TELEGRAM_CHAT_ID=<numeric chat ID or @channelname>
CHRONOARB_TELEGRAM_BOT_USERNAME=<bot username, for the linked-account flow>
CHRONOARB_WEB_BASE_URL=http://localhost:3000
```

The settings loader also accepts bare `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
environment variables. To find a chat ID, message the bot once and open
`https://api.telegram.org/bot<TOKEN>/getUpdates`; the `chat.id` field is the value.

Notifications are sent by a dispatcher process, separate from the API. It drains
pending `alert_deliveries` rows whose channel is `telegram` and consumes
`notification.test_requested` outbox events (written by the alert-rule test
route):

```powershell
# One pass (useful for smoke tests or cron)
python -m apps.api.notifications --once

# Keep running while the API is up
python -m apps.api.notifications --interval 15

# Verify the bot token and chat ID with a single test message
python -m apps.api.notifications --test-message
```

To verify end-to-end from the web app, open **Alerts**, pick a rule whose channels
include `telegram`, and choose **Test**. The dispatcher must be running for the
message to arrive. If neither a user-linked Telegram chat nor
`CHRONOARB_TELEGRAM_CHAT_ID` exists, the dispatcher records the delivery as
`suppressed` rather than retrying forever.