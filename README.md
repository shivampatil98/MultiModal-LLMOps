# MultiModal-LLMOps

An agentic LLMOps pipeline: ingest a YouTube video, extract every spoken word and on-screen frame, then audit it against a regulatory knowledge base with a RAG-powered LLM.

## 🎯 What This Is

You give it a YouTube URL. A minute or two later, you get back a structured compliance report — every violation found in the video, mapped to the specific regulatory rule it breaks, with severity ratings and a summary verdict.

Behind that single API call is a stateful LangGraph workflow that downloads the video, ships it to Azure Video Indexer for multimodal extraction (speech-to-text + OCR + scene analysis), runs a similarity search against a vector store of compliance rules in Azure AI Search, and feeds the retrieved rules to GPT-4o as grounded context for the audit.

Built from scratch to learn what production-grade agentic systems actually look like — token caching, state reducers, RAG retrieval tuning, the works.

## 📦 Project Structure

```
MultiModal-LLMOps/
│
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   └── telemetry.py        # LangSmith / OpenTelemetry setup
│   │   │
│   │   ├── graph/
│   │   │   ├── state.py            # VideoAuditState TypedDict + reducers
│   │   │   ├── nodes.py            # Indexer + Auditor node implementations
│   │   │   └── workflow.py         # LangGraph compilation
│   │   │
│   │   └── services/
│   │       └── video_indexer.py    # Azure VI client (ARM token → VI token)
│   │
│   └── ...
│
├── main.py                         # FastAPI app: /audit, /health
├── pyproject.toml                  # uv-managed dependencies
├── uv.lock                         # Pinned dependency tree
├── .python-version                 # 3.13
└── README.md
```

## 🚀 Running Locally

### 1. Clone and install

```bash
git clone https://github.com/shivampatil98/MultiModal-LLMOps.git
cd MultiModal-LLMOps
uv sync
```
### 2. Configure environment

Create a `.env` file at the repo root:

```bash
# Azure AD service principal (used by DefaultAzureCredential)
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-sp-client-id>
AZURE_CLIENT_SECRET=<your-sp-secret>

# Azure Video Indexer (ARM-based account)
AZURE_SUBSCRIPTION_ID=<sub-id>
AZURE_RESOURCE_GROUP=<rg-name>
AZURE_VI_NAME=<vi-account-name>
AZURE_VI_ACCOUNT_ID=<vi-account-guid>
AZURE_VI_LOCATION=<region>

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<your-aoai>.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
AZURE_SEARCH_API_KEY=<admin-key>
AZURE_SEARCH_INDEX_NAME=compliance-rules

# LangSmith (optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<langsmith-key>
LANGCHAIN_PROJECT=multimodalComplianceQA
```

The service principal needs **Contributor** (or a custom role with `Microsoft.VideoIndexer/accounts/generateAccessToken/action`) scoped to the Video Indexer account. Without it, the indexer node 403s and the workflow silently produces an empty audit.

### 3. Run

```bash
uv run uvicorn main:app --reload
```

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`


---
## 🔬 Techniques Used

| Technique | Why |
|---|---|
| **TypedDict state + `Annotated[List, operator.add]`** | LangGraph reducers let multiple nodes append to the same list (errors, compliance_results) instead of overwriting. Critical for fan-out designs. |
| **Two-step Azure token exchange** | ARM token → `generateAccessToken` → VI account token. The exact dance Microsoft requires for ARM-based Video Indexer accounts. |
| **`DefaultAzureCredential`** | Same code works locally (env vars), in containers (managed identity), and in CI (workload identity). No `if PROD: ...` branching. |
| **RAG over compliance rules** | Rules live in a vector store, not the prompt. Adding new regulations means re-indexing — no code change, no prompt bloat. |
| **`temperature=0.0` on the auditor** | Compliance verdicts must be deterministic. Same input → same output. |
| **Strict JSON schema in system prompt + regex fence-stripping** | LLMs wrap JSON in markdown fences even when told not to. Regex extracts the payload; `json.loads` validates. |
| **Defensive `.get()` chains in extraction** | Azure VI's JSON shape varies by content type (no faces detected → no `faces` key). Chained `.get("x", default)` traversal never crashes. |
| **`load_dotenv(override=True)`** | `.env` wins over shell env vars. Predictable behavior across machines. |

---
⚠️ Disclaimer
Built as a learning project to demonstrate end-to-end LLMOps patterns — agent orchestration, multimodal extraction, RAG, Azure auth, and observability. The compliance categories and severity levels are illustrative; this is not a substitute for legal review or a certified brand-safety service.
---

*Built as part of an AI/ML engineering learning journey.*
