# AI-Powered Code Review Assistant

Automatically reviews GitHub pull requests using an LLM (Groq or local Ollama) and posts
inline review comments directly on the diff. A React dashboard lets you track issues across
repositories over time.

## Architecture

```
GitHub PR Event → Webhook Handler → Diff Parser → Review Engine → LLM Provider
                                                                 ↓
                                         GitHub inline comments ← GitHub Client
                                                                 ↓
                                                          PostgreSQL → Dashboard API → React UI
```

## Quick Start (Docker Compose)

### 1. Clone and configure

```bash
git clone <your-repo-url> ai-code-reviewer
cd ai-code-reviewer
cp .env.example .env
# Edit .env and fill in your secrets
```

### 2. Start services

```bash
docker compose up --build
```

| Service  | URL                    |
|----------|------------------------|
| API      | http://localhost:8000  |
| Frontend | http://localhost:5173  |
| Postgres | localhost:5432         |

### 3. Expose the webhook endpoint (local dev)

Install [ngrok](https://ngrok.com/) then:

```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g. `https://abc123.ngrok.io`) and add a GitHub webhook:

- **Payload URL**: `https://abc123.ngrok.io/webhook/github`
- **Content type**: `application/json`
- **Secret**: the value of `GITHUB_WEBHOOK_SECRET` in your `.env`
- **Events**: select **Pull requests**

## Environment Variables

| Variable               | Required | Description                                         |
|------------------------|----------|-----------------------------------------------------|
| `GITHUB_WEBHOOK_SECRET`| ✅       | HMAC secret shared with GitHub                      |
| `GITHUB_TOKEN`         | ✅       | Personal access token (needs `repo` scope)          |
| `LLM_PROVIDER`         | ✅       | `groq` or `ollama`                                  |
| `GROQ_API_KEY`         | ✅*      | Free at [console.groq.com](https://console.groq.com)|
| `OLLAMA_BASE_URL`      |          | Default: `http://localhost:11434`                   |
| `DATABASE_URL`         | ✅       | asyncpg connection string                            |

\* Required when `LLM_PROVIDER=groq`

## LLM Providers

### Groq (default, free tier)
- Model: `llama-3.3-70b-versatile`
- Sign up at [console.groq.com](https://console.groq.com) — no credit card required
- Automatically falls back to Ollama on rate-limit

### Ollama (local fallback)
- Model: `codellama`
- Install: https://ollama.com
- Run: `ollama pull codellama`

## Review Categories & Severities

| Category      | Examples                                      |
|---------------|-----------------------------------------------|
| `security`    | SQL injection, hardcoded secrets, XSS         |
| `bug`         | Off-by-one errors, null dereferences          |
| `performance` | N+1 queries, unnecessary allocations          |
| `architecture`| Tight coupling, missing abstractions          |
| `style`       | Naming, formatting, dead code                 |

| Severity   | Meaning                                      |
|------------|----------------------------------------------|
| `critical` | Must fix before merging                      |
| `warning`  | Should fix — notable risk or debt            |
| `info`     | Suggestion / nice-to-have                   |

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env  # fill in values
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database migrations (Alembic)

```bash
cd backend
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

## Project Structure

```
ai-code-reviewer/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint
│   │   ├── config.py                # Pydantic settings
│   │   ├── api/
│   │   │   ├── webhooks.py          # POST /webhook/github
│   │   │   └── dashboard.py        # GET /api/repos, /reviews, /metrics
│   │   ├── core/
│   │   │   ├── diff_parser.py      # Parse unified diff → DiffHunk objects
│   │   │   ├── review_engine.py    # Orchestrate LLM + GitHub posting
│   │   │   └── llm/
│   │   │       ├── base.py         # Abstract LLMProvider
│   │   │       ├── groq_provider.py
│   │   │       └── ollama_provider.py
│   │   ├── github/
│   │   │   ├── client.py           # PyGithub wrapper
│   │   │   └── webhook_validator.py
│   │   └── db/
│   │       ├── models.py           # SQLAlchemy ORM
│   │       ├── session.py          # Async session factory
│   │       └── migrations/         # Alembic migrations
│   ├── requirements.txt
│   ├── alembic.ini
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx       # Repository list
│   │   │   ├── RepoDetail.tsx      # Per-repo metrics + review history
│   │   │   └── ReviewDetail.tsx    # Individual PR comments
│   │   ├── components/
│   │   │   ├── MetricCard.tsx
│   │   │   ├── IssueChart.tsx
│   │   │   └── ReviewTable.tsx
│   │   └── api/client.ts           # Typed Axios API client
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```
