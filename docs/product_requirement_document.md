
**Project idea: Multi-tenant SaaS Knowledge Assistant**

Imagine you run one SaaS product, and different companies upload their own docs:

* Company A uploads HR policies, onboarding docs, engineering runbooks
* Company B uploads sales playbooks, contracts, SOPs
* Company C uploads legal docs and support knowledge base

Each company should only see **its own data**. Within each company, access is further restricted by user role.

---

## What to build

### Core user story

A user logs in and asks:

> “What is our PTO policy?”
> “How do I deploy to production?”
> “Show refund policy for enterprise customers”

The system:

1. Identifies user
2. Determines:

   * `tenant_id`
   * `user_role`
3. Retrieves only allowed chunks from vector DB
4. Generates answer with citations
5. Tracks tokens/cost
6. Caches repeated queries

---

# Example architecture

```text
Frontend
   ↓
FastAPI / Django API
   ↓
Auth middleware
   ↓
RAG service
   ├── Embed query
   ├── Vector search (pgvector)
   ├── Tenant + role filtering
   ├── LLM answer generation
   ├── Citation formatting
   ├── Token tracking
   └── Cache
```

---

# Database schema

## Users

```sql
users
-----
id
email
tenant_id
role
```

Roles:

* admin
* manager
* employee

---

## Documents

```sql
documents
---------
id
tenant_id
title
uploaded_by
created_at
```

---

## Document chunks

This is where pgvector lives.

```sql
document_chunks
---------------
id
document_id
tenant_id
content
embedding vector(1536)
chunk_index
access_level
metadata jsonb
```

Example `access_level`:

* public
* manager_only
* admin_only

---

## Query logs

Track usage.

```sql
query_logs
----------
id
user_id
tenant_id
query
prompt_tokens
completion_tokens
total_cost
latency_ms
created_at
```

---

## Cache table (optional)

```sql
query_cache
-----------
cache_key
response
expires_at
```

Or use Redis.

---

# Example documents

Upload these sample docs:

### Tenant A: Acme Corp

**Employee handbook**

* PTO policy
* Holidays
* Work from home

**Engineering runbook**

* Deployment steps
* Incident response

---

### Tenant B: Beta Inc

**Sales handbook**

* Pricing tiers
* Refund rules
* Enterprise discount policy

---

This lets you test tenant isolation.

---

# Example permission rules

## Employee asks:

> How do I access payroll?

Can retrieve:

* public
* employee docs

Cannot retrieve:

* manager_only
* admin_only

---

## Manager asks:

> Show salary review process

Can retrieve:

* public
* manager_only

Cannot retrieve:

* admin_only

---

## Admin asks:

> Show acquisition strategy

Can retrieve everything.

---

# Example retrieval query

With PostgreSQL + pgvector:

```sql
SELECT *
FROM document_chunks
WHERE tenant_id = :tenant_id
AND access_level IN (:allowed_roles)
ORDER BY embedding <=> :query_embedding
LIMIT 5;
```

This is the heart of multi-tenant secure RAG.

---

# Example API endpoints

### Upload document

```http
POST /documents/upload
```

Flow:

* parse PDF/text
* chunk
* embed
* save to pgvector

---

### Ask question

```http
POST /chat/query
```

Body:

```json
{
  "query": "What is our refund policy?"
}
```

Response:

```json
{
  "answer": "Enterprise refunds are available within 30 days...",
  "citations": [
    {
      "document": "sales_policy.pdf",
      "chunk": 4
    }
  ],
  "tokens": {
    "prompt": 1200,
    "completion": 220
  }
}
```

---

# Features to implement

## 1. Multi-tenant filtering

Before retrieval:

```python
filters = {
    "tenant_id": user.tenant_id
}
```

No tenant leakage.

This is non-negotiable.

---

## 2. Role-based access

Allowed access:

```python
ROLE_ACCESS = {
    "employee": ["public"],
    "manager": ["public", "manager_only"],
    "admin": ["public", "manager_only", "admin_only"],
}
```

---

## 3. Citations

Return chunk sources:

```python
sources = [
    {
        "doc": chunk.document.title,
        "chunk": chunk.chunk_index
    }
]
```

Answer:

> PTO is 20 days annually [Employee Handbook, chunk 3]

---

## 4. Retry logic

LLM failures happen.

Use:

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def call_llm():
    ...
```

---

## 5. Token tracking

Track costs:

```python
usage = response.response_metadata["token_usage"]
```

Store in DB.

---

## 6. Caching

Hash:

```python
cache_key = f"{tenant_id}:{role}:{query}"
```

Check cache first.

---

# LangChain pieces

Use:

### embeddings

```python
OpenAIEmbeddings()
```

---

### vector store

```python
PGVector
```

---

### retriever

```python
vectorstore.as_retriever()
```

But customize retrieval with SQL filters.

---

### chain

```python
RetrievalQA
```

or LCEL runnable pipeline.

---

# Nice stretch goals

After MVP:

### conversation memory

Store chat history per tenant.

---

### document versioning

If handbook changes:

* old version archived
* re-embed new version

---

### feedback system

Thumbs up/down on answers.

---

### analytics dashboard

Show:

* top queries
* cost per tenant
* failed queries

---

# Final project folder

```text
rag-saas/
├── api/
├── auth/
├── ingestion/
├── retrieval/
├── llm/
├── cache/
├── models/
├── migrations/
└── tests/
```

---
A realistic MVP demo:

1. Create 2 tenants
2. Create 3 users with different roles
3. Upload 5 docs
4. Ask same question from different users
5. Observe different answers due to filtering

That demonstrates:

* security
* retrieval quality
* production concerns
