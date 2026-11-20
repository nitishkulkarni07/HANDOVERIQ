# HandoverIQ — Round 3 knowledge continuity platform

Evidence-grounded project handovers for teams with role changes: **Reconstruct → Verify → Approve → Continue**.

**Live:** https://handoveriq-three.vercel.app  
**Source:** https://github.com/nitishkulkarni07/HANDOVERIQ

> Hackathon demonstration: use only authorized or synthetic project documents. Do not upload confidential personal information.

## What works / what is optional

| Area | Implementation | Important boundary |
| --- | --- | --- |
| Login | Three demo roles: lead, reviewer, newmember; PBKDF2 password hashing and signed, expiring sessions | This is demonstration auth, **not** Supabase Auth/enterprise SSO |
| Document ingestion | PDF, DOCX, TXT, MD; 2 MB and 30-page PDF limit; source lines and visibility flags | Scanned PDF OCR is **not** supported |
| AI document assistant | Permission-filtered evidence with citations, Ollama or Gemini, search fallback | Model output can be wrong; always verify citations |
| Semantic retrieval | pgvector(768) index with Gemini text embeddings (or matching-dimension Ollama embeddings) | Use **Build semantic index** per document; up to four sections per click; lexical fallback otherwise |
| Decision DNA / Gap Radar | Timeline of detected decisions, source references, missing-rationale flags; gap questions | Heuristic/rule-based, not verified reasoning about alternatives |
| Review / approval | Drafts, accept/reject/correct per claim, publish, Markdown export | Approval requires reviewing every claim |
| Onboarding | Seven role-aware steps with persisted per-user completion and acknowledgement | Plan contents are generated from categories, not personalized LLM coaching |

## Local installation

Requirements: Python 3.12+, pip. Clone the GitHub repository:

```bash
git clone https://github.com/nitishkulkarni07/HANDOVERIQ.git
cd HANDOVERIQ
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Configure environment variables in your shell (do not commit secrets):

- `DEMO_PASSWORD`: a long secret password to use for all three demo users.
- `AUTH_SECRET`: another independent, random secret string for signed authentication tokens.
- `DATABASE_URL`: PostgreSQL connection string. If absent, the app uses a local SQLite file named `handoveriq.sqlite3`.
- `GEMINI_API_KEY` (optional): Google Gemini API key for cloud answer generation and 768-dimensional embeddings.
- `GEMINI_MODEL` (optional): a Gemini generateContent model supported by your account; the application's default may need overriding.
- `OLLAMA_URL` (optional): reachable Ollama endpoint, e.g. `http://127.0.0.1:11434` for a local developer machine.
- `OLLAMA_MODEL` (optional): installed Ollama chat model, default `llama3.2`.
- `OLLAMA_EMBED_MODEL` (optional): Ollama embedding model that produces exactly **768 dimensions** (default `nomic-embed-text`).
- `OLLAMA_API_KEY` (optional): API key for a hosted Ollama endpoint.
- `HANDOVERIQ_DEMO_MODE` (optional): set to 1 only to override the hosted DB with temporary SQLite; **never for persistent production**.

Run:

```bash
python -m uvicorn app:app --reload
```

Visit http://127.0.0.1:8000 and log in as `lead`, `reviewer`, or `newmember` using `DEMO_PASSWORD`.

### Ollama setup

Install [Ollama](https://ollama.com/), run `ollama pull llama3.2`, start `ollama serve` (if it is not already running), and select **Ollama only** in AI Assistant. The Ollama API is used server-side at `/api/chat`, **not** directly from the browser. Ollama docs: https://docs.ollama.com/api .

**Vercel cannot access Ollama running on your laptop at localhost.** For hosted Ollama, configure `OLLAMA_URL` to a reachable HTTPS endpoint with appropriate authentication, otherwise choose Gemini/search. Never expose an unauthenticated Ollama server publicly.

### PostgreSQL / Supabase

The existing Supabase project uses the private `handoveriq` schema, including users, sources, handovers, receipts, `source_embeddings` (pgvector) and `onboarding_progress`. An initial migration is in Supabase; use your own provisioned database and recreate the schema as needed.

For Supabase shared pooler, `DATABASE_URL` must be the **PostgreSQL** connection string, not the Supabase publishable key. Percent-encode special characters in the DB password. Never log full connection strings.

Local SQLite supports upload, chat lexical retrieval, approvals and onboarding progress. Semantic indexing requires PostgreSQL with pgvector, and an embedding provider.

## Main journey for judges

1. Log in as **lead** and upload a sample TXT/PDF containing decision, task, blocker, risk and owner information.
2. Open the document; confirm the numbered evidence lines. In PostgreSQL, use **Build semantic index** to index up to four sections per call and repeat until complete.
3. Open **AI Assistant**, ask about an uploaded decision, review the cited evidence. Try **Ollama only** when a server is configured; use auto otherwise.
4. Open **Decision Timeline** to see decisions, citations and missing-rationale flags.
5. Create a new handover for incoming members, accept/correct/reject **each** claim, then approve.
6. Sign out; sign in as **newmember**, inspect the approved handover and check off the seven onboarding tasks. Acknowledge receipt after completion.
7. Refresh and revisit the same handover to confirm saved state. Repeat acknowledgement to check idempotency.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The automated SQLite journey covers sign-in errors, empty states, upload/refresh, source access permissions, handover review and approval, duplicate acknowledgement, day-by-day progress, and unsupported uploads. Provider networking and cloud persistence require separate manual checks.

## Architecture

Browser HTML/CSS/JavaScript → FastAPI REST endpoints → PostgreSQL via psycopg (or SQLite locally).
Authorized uploads → extraction (pypdf/python-docx) → source lines → rule-based tagged claims and gaps → reviewer approval → role-specific handover → personal onboarding progress.
Chat retrieves relevant source lines by lexical matching and, if indexed, pgvector cosine similarity. Ollama `/api/chat` or Gemini `generateContent` produces an answer grounded in provided evidence. Failure falls back to cited excerpts in auto mode.

## Round 3 commitments / disclosure

1. **RAG with source citations:** pgvector schema, document indexing endpoint, semantic retrieval + lexical fallback, configured Ollama/Gemini answer generation. Manual index creation is still required; embedding performance depends on API availability.
2. **Decision tracking:** evidence-linked decision timeline and missing rationale questions. The pipeline still relies on heuristic extraction rather than a full autonomous decision graph.
3. **Review → onboarding:** persisted seven-step progress per user and acknowledgement gated on completion for incoming members.

These are the implementations, not claims of perfect AI accuracy. Evaluate the complete journey before declaring production readiness.

## Roadmap

- Better automatic/batch vector indexing and source-change invalidation.
- Time-ordered provenance graph, owner resolution and contradiction detection.
- OCR for scanned documents and broader supported formats.
- Enterprise authentication, granular ACLs, audit trails, multi-workspace isolation.
- Integration test suite running against a staging PostgreSQL database and load/latency checks.

Built with AI assistance; disclose work provenance accurately under hackathon event-window rules.
