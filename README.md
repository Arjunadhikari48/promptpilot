# PromptPilot

PromptPilot is a personal prompt library and AI playground. It lets each account save prompts, search and organize them with tags, review prior prompt content, restore a previous version, and send prompts to Groq-hosted language models.

The application is a single FastAPI service. It serves the browser UI and JSON API from the same origin, stores users/prompts/versions in SQLite by default, and calls Groq on the server so the provider key is never sent to the browser.

## Contents

- [What you can do](#what-you-can-do)
- [How the app works](#how-the-app-works)
- [Project layout](#project-layout)
- [Requirements](#requirements)
- [Run locally on Windows](#run-locally-on-windows)
- [Run locally on macOS or Linux](#run-locally-on-macos-or-linux)
- [Configuration](#configuration)
- [Use the web app](#use-the-web-app)
- [HTTP API guide](#http-api-guide)
- [Run with Docker Compose](#run-with-docker-compose)
- [Database and prompt versions](#database-and-prompt-versions)
- [Development and tests](#development-and-tests)
- [Troubleshooting](#troubleshooting)
- [Current limitations](#current-limitations)

## What you can do

- **Create an account and sign in.** Passwords are stored as bcrypt hashes. Successful sign-in returns a bearer token that the web UI keeps in browser local storage.
- **Save and manage prompts.** A prompt has a title, optional description, content, and optional comma-separated tags. You can create, edit, delete, and run a saved prompt in the playground.
- **Search your prompt titles.** Search is scoped to the signed-in account and currently checks titles only.
- **Review and restore versions.** New prompts start at version 1. A new version is recorded when the prompt content changes. Restoring a previous version copies its content into the current prompt and adds a new version entry.
- **Try AI models.** The playground can run one Groq model or compare several models against the same prompt. The current UI offers Groq-hosted GPT OSS 120B, GPT OSS 20B, and Qwen 3.8 27B model IDs. Model availability can depend on your Groq account and can change over time.

Prompt library features work without a Groq key. The playground requires a valid `GROQ_API_KEY` in the server environment.

For a visual walkthrough of the features, architecture, setup, API, deployment, and project limits, see [PromptPilot_Project_Guide.pptx](PromptPilot_Project_Guide.pptx) in this repository.

## How the app works

1. The browser loads `app/static/index.html` from FastAPI.
2. Registration and login call the `/api/v1/auth` endpoints. Login returns a signed JWT.
3. Browser API requests include `Authorization: Bearer <token>`.
4. The API looks up prompts using the authenticated user's ID, so one account cannot read or change another account's prompts.
5. SQLAlchemy reads and writes data in the configured database. For a new local setup, the default is `promptpilot.db` in the project directory.
6. LLM requests go from the FastAPI server to Groq using `GROQ_API_KEY`; the key is not included in browser code or API responses.

## Project layout

```text
promptpilot/
├── app/
│   ├── api/
│   │   ├── deps.py                 # JWT authentication and current-user dependency
│   │   └── v1/
│   │       ├── auth.py             # Account registration and login
│   │       ├── llm.py              # Run and compare model endpoints
│   │       ├── prompts.py          # Prompt create/read/update/delete and search
│   │       └── versions.py         # Version history, detail, and restore endpoints
│   ├── core/
│   │   ├── config.py               # Environment-based application settings
│   │   ├── database.py             # SQLAlchemy engine, sessions, and Base
│   │   └── security.py             # Password hashing and JWT helpers
│   ├── models/
│   │   ├── user.py                 # User database model
│   │   └── prompt.py               # Prompt and PromptVersion database models
│   ├── schemas/
│   │   ├── user.py                 # User and token request/response schemas
│   │   ├── prompt.py               # Prompt request/response schemas
│   │   └── version.py              # Prompt version response schemas
│   ├── services/
│   │   ├── llm_service.py          # Groq-compatible model client and call logic
│   │   └── prompt_service.py       # Prompt lookup helper
│   ├── static/
│   │   └── index.html              # Browser UI, styles, and frontend logic
│   └── main.py                     # FastAPI app, table creation, and route setup
├── tests/
│   ├── test_auth.py                # Authentication tests
│   └── test_prompts.py             # Prompt API tests
├── .env.example                    # Safe configuration template
├── .gitignore                      # Excludes local secrets, databases, and caches
├── Dockerfile                      # Container image definition
├── docker-compose.yml              # App service and persistent SQLite volume
├── README.md
└── requirements.txt                # Python package requirements
```

Local-only files such as `.env`, `venv/`, and `promptpilot.db` are intentionally not part of the source tree documentation above.

## Requirements

- Python 3.10 or newer
- Internet access during initial package installation
- A Groq API key to use the AI playground
- Optional: Docker Desktop with Compose for containerized use

## Run locally on Windows

Open PowerShell in the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set a unique secret key and your Groq key. For example, generate a secret with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into `SECRET_KEY`. Then start the development server:

```powershell
python -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. If port 8000 is busy, choose another port, for example:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

When you use an existing virtual environment, activate that environment first or call its interpreter directly, for example `venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001`.

## Run locally on macOS or Linux

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Put the generated value in `SECRET_KEY`, add your Groq key, then run:

```bash
python -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. If necessary, add `--port 8001` to the Uvicorn command.

## Configuration

Settings are loaded from environment variables and `.env` in the current working directory. `.env.example` documents the expected values:

| Variable | Required | Purpose |
| --- | --- | --- |
| `APP_NAME` | No | App title returned by the health endpoint; defaults to `PromptPilot`. |
| `SECRET_KEY` | Yes | At least 32 characters; signs and validates access tokens. Use a private random value. |
| `ALGORITHM` | No | JWT signing algorithm; defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Access-token lifetime; defaults to 60 minutes. |
| `DATABASE_URL` | No | SQLAlchemy database URL; defaults to `sqlite:///./promptpilot.db`. |
| `GROQ_API_KEY` | For AI features | Secret key used by the server to call Groq. Leave empty to disable AI requests. |
| `GROQ_BASE_URL` | No | OpenAI-compatible Groq API base URL; defaults to `https://api.groq.com/openai/v1`. |

Do not commit `.env` or paste its contents into issue reports. If a provider key has been exposed, revoke it and create a replacement.

## Use the web app

1. Open the app root URL (for example, `http://127.0.0.1:8000/`).
2. Choose **Register**, submit an email and a password of at least 8 characters, then sign in. Passwords may be up to 72 characters because of bcrypt's input limit.
3. In **Prompts**, choose **New Prompt**, enter a title and content, and optionally fill in the description and comma-separated tags.
4. Select **Edit** on a prompt to update its fields and see its version history. Changing the content creates a version; changing only its title, description, or tags does not.
5. Use the search box to find prompts by title. **Run** copies a prompt's content into the playground.
6. In **Playground**, choose a model and token limit, then select **Run** or **Compare 2 Models**. The API token is required, and a configured Groq key is needed for generation.
7. Select **Restore this version** in the history to make that content current. Restoring also creates a new version, preserving the history of the restore action.

The browser stores the login token in local storage until it expires or you log out. Logging out removes it from that browser.

## HTTP API guide

The API prefix is `/api/v1`. Interactive docs are at `/docs`; the OpenAPI schema is at `/openapi.json`. Except for registration and login, routes below require:

```http
Authorization: Bearer <access_token>
```

### Authentication

| Method and path | Description |
| --- | --- |
| `POST /auth/register` | Create an account. JSON body: `{"email":"person@example.com","password":"at-least-8-chars"}`. |
| `POST /auth/login` | Sign in using form fields `username` (email) and `password`; returns `access_token` and `token_type`. |

Example using curl:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"person@example.com","password":"example-password-123"}'

curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=person@example.com' \
  --data-urlencode 'password=example-password-123'
```

Copy `access_token` from the login response for the following requests. Treat it as a password; do not publish it.

### Prompts

| Method and path | Description |
| --- | --- |
| `POST /prompts` | Create a prompt and its first version. Required JSON: `title`, `content`; optional: `description`, `tags`. |
| `GET /prompts` | List your prompts. Optional query parameters: `q` (title search), `skip` (default 0), `limit` (default 50, maximum 100). |
| `GET /prompts/{prompt_id}` | Read one of your prompts. |
| `PUT /prompts/{prompt_id}` | Update supplied fields. Send only the fields being changed. A changed `content` creates a new version. |
| `DELETE /prompts/{prompt_id}` | Delete a prompt and its versions. Returns `204 No Content`. |

Example create request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/prompts \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{"title":"Friendly email","description":"Draft a warm customer email","content":"Write a friendly email about: {{topic}}","tags":"email, customer"}'
```

### Prompt versions

| Method and path | Description |
| --- | --- |
| `GET /prompts/{prompt_id}/versions` | List version numbers, timestamps, and content previews (newest first). |
| `GET /prompts/{prompt_id}/versions/{version}` | Read the full content of one version. |
| `POST /prompts/{prompt_id}/versions/{version}/restore` | Restore that content and create a new latest version. |

Every version route checks that the prompt belongs to the signed-in account.

### AI playground

| Method and path | Description |
| --- | --- |
| `POST /llm/run` | Run one prompt against Groq. JSON: `{"provider":"groq","model":"openai/gpt-oss-120b","prompt":"...","max_tokens":500}`. |
| `POST /llm/compare` | Compare provider calls. Currently only `groq` is supported; use the model comparison endpoint to compare models. |
| `POST /llm/openai/compare-models` | Compare up to four Groq model IDs. The `openai` segment is a legacy route name; it calls Groq, not OpenAI. |

`max_tokens` must be between 1 and 8000. AI endpoints require a valid Groq key on the server. Provider API failures are returned as `502`; unsupported provider/model configuration errors may return `400` or per-model error details in comparison responses.

### Health check

`GET /health` returns a small JSON status response and does not require authentication. It confirms the app process is responding; it does not verify that Groq credentials work.

## Run with Docker Compose

1. Create `.env` from `.env.example` and set `SECRET_KEY`. Add `GROQ_API_KEY` if you want AI generation.
2. Make sure Docker Desktop/the Docker Engine is running.
3. From the project directory, run:

   ```bash
   docker compose up --build
   ```

4. Open <http://127.0.0.1:8000>.
5. Stop the app with `Ctrl+C`. Run `docker compose down` to stop and remove the container. The named `promptpilot_data` volume remains, so the SQLite database persists across container restarts and rebuilds.

To remove the persistent database as well, run `docker compose down --volumes`. This deletes the stored accounts and prompts; export or back up any data you want to keep before doing so.

## Database and prompt versions

The default local database is `promptpilot.db` in the working directory. `DATABASE_URL` can point SQLAlchemy at another supported database. SQLite connections are configured for FastAPI's threaded request handling.

The app creates missing tables at startup with SQLAlchemy `create_all`. This is convenient for local development, but it does not upgrade existing tables when a schema changes. Back up data and use a migration tool such as Alembic before making production schema changes.

Deleting a prompt also deletes its version rows. Prompt versions contain content snapshots and are only accessible through ownership-checked routes.

## Development and tests

Activate the virtual environment, then install requirements as described above. Start a hot-reloading server with:

```bash
python -m uvicorn app.main:app --reload
```

Run the automated tests with:

```bash
python -m pytest
```

The current tests cover basic registration/login and prompt creation. The test modules import `app.main`, which uses the configured database URL; set a separate test database if you want to isolate test data from a working local database.

## Troubleshooting

- **`SECRET_KEY` validation error:** Set `SECRET_KEY` in `.env` to a random value at least 32 characters long. The app intentionally has no insecure default secret.
- **`python` or the virtual environment cannot start:** Recreate the environment with an installed Python 3.10+ interpreter, then reinstall requirements. On Windows, use `\.venv\Scripts\python.exe` to address the intended environment explicitly.
- **Port 8000 is busy:** Start Uvicorn with `--port 8001` (or another available port) and open that port in the browser.
- **Login returns 401:** Check the email/password pair. Login sends the email in the OAuth2 form field named `username`.
- **Protected API returns 401:** Sign in again and send the token as `Authorization: Bearer <access_token>`. Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`.
- **AI requests fail:** Confirm `GROQ_API_KEY` is set in the server's `.env`, restart the server after changing it, and verify the selected model is enabled for your Groq account.
- **The UI loads but prompt operations fail:** Confirm the browser has a valid login token. Log out and sign in again if the token expired.
- **SQLite permission or path error:** Ensure the process can write to the directory containing the database. For Docker, the Compose volume is mounted at `/app/data`.

## Current limitations

- Groq is the only implemented provider. The `/llm/openai/compare-models` URL is retained for compatibility but does not call OpenAI.
- Prompt search checks titles, not prompt content, descriptions, or tags.
- There is no password reset, email verification, account deletion, team sharing, or role management flow.
- Database tables are created automatically, but there is no migration history yet.
- The default app is intended for local use. A public deployment should use HTTPS, a private strong `SECRET_KEY`, a managed database/backup plan, and operational controls such as rate limiting and monitoring.
