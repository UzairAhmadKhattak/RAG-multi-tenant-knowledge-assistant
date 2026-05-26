# Knowledge Assistant

A multi-tenant RAG (Retrieval-Augmented Generation) API that lets organizations upload documents, search them with vector similarity, and chat with an AI assistant grounded in their own knowledge base. Access is scoped by organization and user role.

---

## What We Built

### Core capabilities

| Feature | Description |
|--------|-------------|
| **Authentication** | JWT-based login with bcrypt password hashing. Protected routes require a Bearer token. |
| **Document upload** | Upload PDF, plain text, DOCX, or ODT files. Files are validated by MIME type (`python-magic`), stored on disk, and indexed in the database. |
| **Document summarization** | On upload, GPT-4o-mini summarizes the document from first, middle, and last page excerpts. The summary is stored on the `documents` row and used at query time for richer context. |
| **Vector indexing** | Documents are chunked (500 chars, 50 overlap), embedded with OpenAI `text-embedding-3-small` (1536 dimensions), and stored in PostgreSQL via **pgvector**. |
| **Role-based access** | Chunks carry an `access_level` in JSON metadata. Employees, managers, and admins each see only chunks their role allows. |
| **RAG chat** | User questions are embedded, top-5 similar chunks are retrieved (cosine distance), combined with document summaries and chat history, then answered by GPT-4o-mini. |
| **Conversation memory** | Messages are grouped in conversations. After 10 turns, older messages are summarized into `conversation.summary` so long chats stay within context limits. |
| **Usage tracking** | Each assistant reply logs prompt/completion tokens, latency, and estimated cost in `query_logs`, linked to the message. |

### API surface

All routes are under `/api/v1`.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/auth/login` | No | Login (`username` + `password` as OAuth2 form). Returns access and refresh JWTs. |
| `POST` | `/docs/upload` | Yes | Upload or update a document (`file`, `title`, `role` as multipart form). |
| `POST` | `/chat/` | Yes | Ask a question (`query`, optional `conversation_id`). Returns answer and `conversation_id`. |

Interactive docs: `http://localhost:8000/docs` when the server is running.

---

## How We Built It

### Architecture

```
Client
  │
  ▼
FastAPI (src/app/main.py)
  ├── /api/v1/auth     → auth_service (JWT + bcrypt)
  ├── /api/v1/docs     → upload → summarize → chunk → embed → pgvector
  └── /api/v1/chat     → embed query → vector search → LangChain → GPT-4o-mini
         │
         ▼
PostgreSQL + pgvector
  organizations → users → documents → document_chunks (embeddings)
                      └── conversations → messages → query_logs
```

### Tech stack

- **Runtime**: Python 3.13, [uv](https://github.com/astral-sh/uv) for dependency management
- **API**: FastAPI with async endpoints
- **ORM**: SQLAlchemy 2.0 (async) + `asyncpg`
- **Migrations**: Alembic (sync driver `psycopg` for migrations; `asyncpg` for the app)
- **Vectors**: `pgvector` extension + `pgvector` Python package
- **AI**: LangChain + LangChain OpenAI (`ChatOpenAI`, `OpenAIEmbeddings`)
- **Auth**: PyJWT, bcrypt, OAuth2 password flow

### Key design decisions

1. **Organization isolation** — Every document chunk and vector search is filtered by `organization_id`, so tenants never see each other's data.

2. **Role-based retrieval** — On upload, the uploader's role determines which `access_level` tags are written into chunk `meta_data`. At query time, `search_vectors` only returns chunks whose metadata matches the user's allowed levels (`ROLE_ACCESS` in `src/app/core/constants.py`).

3. **Buffered embedding** — Large files are loaded lazily (PDF/text/DOCX/ODT loaders) and processed in batches of 5 pages (`BUFFER_SIZE`) to limit memory use before chunking and embedding.

4. **Context assembly** — Retrieved chunks are formatted with their parent document's title and summary, not just raw text, so the LLM understands document-level intent.

5. **Rolling chat summary** — When a conversation hits 10 messages, those messages are summarized and stored on the conversation; newer turns still pass the last 10 message pairs into the prompt for short-term context.

6. **Schema evolution** — The database started with separate user/assistant message rows and query text on `query_logs`. Migrations refactored to paired `user_query` / `assistant_response` on `messages`, document summaries, nullable conversation summaries, and `query_logs` tied to `message_id` only.

---

## Project Setup

### Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL 15+ with the **pgvector** extension
- OpenAI API key
- `libmagic` (for `python-magic` file type detection)

On Ubuntu/Debian:

```bash
sudo apt install libmagic1
```

### 1. Clone and install dependencies

```bash
cd "knowlege assistant"
uv sync
```

This creates `.venv` and installs packages from `pyproject.toml` / `uv.lock`.

### 2. Environment variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=knowledge_assistant
OPENAI_API_KEY=sk-...
SECRET_KEY=your-long-random-secret-for-jwt
```

`Settings` in `src/app/core/config.py` loads these automatically. `DATABASE_URL` is built as `postgresql+asyncpg://...`.

### 3. Run the API

From the project root:

```bash
uv run uvicorn src.app.main:app --reload
```

Or with the virtualenv activated:

```bash
.venv/bin/uvicorn src.app.main:app --reload
```

Uploaded files are stored under `src/uploads/` (created automatically).

---

## Database Setup

### 1. Create the database

```bash
sudo -u postgres psql
```

```sql
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
CREATE DATABASE knowledge_assistant OWNER your_db_user;
\c knowledge_assistant
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

The `vector` extension is required for `document_chunks.embedding` (`VECTOR(1536)`).

### 2. Run migrations

Alembic reads the DB URL from your `.env` (via `settings.DATABASE_URL`, using the `psycopg` driver for migrations):

```bash
uv run alembic upgrade head
```

Migration history (in order):

| Revision | Change |
|----------|--------|
| `275b56a80256` | Initial schema: organizations, users, documents, chunks, conversations, messages, query_logs |
| `4ba03c2f7292` | Add `summary` to documents |
| `d63c4e01939d` | Make `conversations.summary` nullable |
| `1586f71fdd46` | Query logs link to `message_id` instead of user/conversation |
| `705db0040a0d` | Messages store `user_query` + `assistant_response` (drop role/content columns) |
| `1eddfdc812b0` | Remove redundant `query` column from query_logs |

To generate a new migration after model changes:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

### 3. Seed a test user (optional)

```bash
uv run python -m src.app.db.seed_user
```

This creates:

- Organization: `Test Org`
- User: `test` / `1234` (admin role)

Use these credentials at `POST /api/v1/auth/login` (form fields `username` and `password`).

---

## Database Schema (current)

```
organizations
  └── users (role: admin | manager | employee)
  └── documents (title, file_path, summary, uploaded_by)
        └── document_chunks (content, embedding vector(1536), meta_data JSONB)
  └── conversations (title, summary, user_id)
        └── messages (user_query, assistant_response)
              └── query_logs (tokens, latency_ms, cost)
```

**Enums**

- `UserRole`: `admin`, `manager`, `employee`
- Chunk `meta_data.access_level`: role-derived list, e.g. `["employee_only"]` or `["employee_only", "manager_only", "admin_only"]`

---

## Example Workflow

1. **Login**

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test&password=1234"
   ```

2. **Upload a document**

   ```bash
   curl -X POST http://localhost:8000/api/v1/docs/upload \
     -H "Authorization: Bearer <access_token>" \
     -F "file=@./my-doc.pdf" \
     -F "title=Company Handbook" \
     -F "role=admin"
   ```

3. **Chat**

   ```bash
   curl -X POST "http://localhost:8000/api/v1/chat/?query=What%20is%20the%20vacation%20policy?" \
     -H "Authorization: Bearer <access_token>"
   ```

   Pass `conversation_id` on follow-up requests to continue the same thread.

---

## Project Layout

```
knowlege assistant/
├── alembic/              # DB migrations
├── src/
│   ├── uploads/          # Uploaded files (gitignored)
│   └── app/
│       ├── api/v1/       # auth, documents, chat routes
│       ├── core/         # config, security, constants
│       ├── db/           # session, seed script
│       ├── models/       # SQLAlchemy models
│       ├── schemas/      # Pydantic response models
│       ├── services/     # auth, embed, chat, summarizer
│       └── utils/        # file save, query helpers
├── pyproject.toml
├── uv.lock
└── .env                  # not committed
```

---

## Supported File Types

| MIME type | Loader |
|-----------|--------|
| `application/pdf` | PyPDFLoader |
| `text/plain` | TextLoader |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Docx2txtLoader |
| `application/vnd.oasis.opendocument.text` | Custom ODT parser (odfpy) |

---

## Notes

- **Re-uploading** a document with the same `title` updates the row and replaces chunk embeddings for that document.
- **Cost fields** on `query_logs` use placeholder GPT-4o-mini rates; adjust in `chat_assistant.py` if pricing changes.
- **Refresh tokens** are issued at login but there is no refresh endpoint yet; only the access token is used for API calls.
- Ensure PostgreSQL has `pgvector` installed (`CREATE EXTENSION vector`) before running migrations, or the initial migration will fail on the `embedding` column.
