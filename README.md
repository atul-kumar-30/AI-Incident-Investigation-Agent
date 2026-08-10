# 🤖 AI Incident Investigation Agent

An evidence-grounded **Agentic AI system for investigating software production incidents** using LangGraph, RAG, tool calling, multi-source evidence collection, and structured hypothesis verification.

Instead of sending an incident directly to an LLM and asking it to guess the root cause, the system performs a multi-step investigation across **application logs, source code, recent Git changes, and operational documents**. It collects evidence, generates competing hypotheses, ranks them, and actively verifies the strongest candidates.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| 🤖 **Agentic AI** | LangGraph, LangChain, LLM Structured Output, Tool Calling |
| 🧠 **LLM** | Google Gemini |
| 🔍 **RAG & Retrieval** | Embeddings, Semantic Search, Lexical Search, Hybrid Retrieval |
| 🗄️ **Vector Database** | PostgreSQL, pgvector |
| ⚙️ **Backend** | Python 3.11, FastAPI, Pydantic v2, Uvicorn |
| 💾 **Database & ORM** | PostgreSQL 15, SQLAlchemy 2.x Async |
| 🔄 **Migrations** | Alembic |
| 🎨 **Frontend** | React, TypeScript, Vite, Tailwind CSS |
| 🐳 **Containerization** | Docker, Docker Compose |
| 🧪 **Testing** | pytest, pytest-asyncio, Testcontainers |
| 🌿 **Version Control** | Git |

---

## 🎯 What Problem Does It Solve?

Production incidents are rarely explained by a single error message.

For example:

> **Why are users getting HTTP 500 errors after login?**

Investigating such an issue may require analyzing application logs, tracing the affected code path, reviewing recent Git changes, and searching operational documentation.

The **AI Incident Investigation Agent** automates this process by collecting evidence from multiple sources, generating competing hypotheses, and actively verifying the strongest candidates before producing an evidence-grounded investigation result.

Rather than simply asking an LLM to guess the root cause, the system preserves evidence provenance, considers contradictory evidence, and makes uncertainty explicit.

---

## ✨ Key Features

### 🤖 Agentic Investigation with LangGraph

LangGraph orchestrates a stateful investigation workflow instead of a single prompt-response call.

The agent can:

- Plan the next investigation step
- Select and execute investigation tools
- Collect and persist evidence
- Perform iterative searches
- Prevent duplicate tool calls
- Enforce iteration limits and tool budgets
- Generate competing hypotheses
- Map evidence to hypotheses
- Rank hypotheses deterministically
- Actively verify high-ranked hypotheses
- Search for supporting and contradictory evidence
- Re-rank hypotheses as new evidence is discovered

---

### 📋 Structured Log Investigation

The system can ingest and search structured application logs using filters such as:

- Service
- Log level
- Endpoint
- HTTP status
- Keywords
- Time ranges
- Trace IDs
- Request IDs

Large result sets are summarized before being passed to the LLM, reducing unnecessary context usage while preserving important patterns.

---

### 💻 Deterministic Code Search

Repositories can be registered, indexed, and associated with incidents.

Source files are split into searchable chunks with metadata such as:

- Repository
- File path
- Programming language
- Symbol
- Line range
- Content hash

The agent can search indexed code using deterministic keyword, path, and symbol-oriented retrieval.

Relevant code evidence preserves file and line-level provenance.

---

### 🌿 Recent Git Change Analysis

The agent can inspect recent Git history to determine whether an incident may correlate with a recent code or configuration change.

Git evidence can include:

- Commit metadata
- Commit timestamps
- Changed files
- Diff summaries
- Relevant configuration changes

This enables the agent to correlate runtime failures with recent repository changes.

---

### 📚 Document & Runbook RAG

Operational documents can be uploaded and indexed for retrieval.

Supported formats include:

- PDF
- Markdown
- TXT

Documents are extracted, chunked, embedded, and stored using **PostgreSQL + pgvector**.

The retrieval system combines:

- Lexical search
- Semantic vector search
- Hybrid retrieval

This allows the agent to search operational runbooks, architecture documentation, troubleshooting guides, and other relevant knowledge during an investigation.

---

### 🔎 Evidence-Grounded Reasoning

Tool outputs are persisted as structured evidence instead of existing only inside the LLM context.

Major evidence sources include:

```text
LOG
CODE
GIT_CHANGE
DOCUMENT
```

Evidence retains provenance so findings can be traced back to their original source.

Before hypothesis generation, collected evidence is synthesized into a compact structured representation containing:

- Runtime signals
- Code findings
- Git/change findings
- Documentation findings
- Timeline clues
- Contradictions
- Known evidence gaps

---

### 🧠 Competing Hypothesis Generation

The system does not immediately declare a single root cause.

Instead, it generates multiple **distinct and testable hypotheses** based on the evidence collected during the investigation.

Evidence is explicitly mapped to hypotheses as:

```text
SUPPORTS
CONTRADICTS
NEUTRAL
```

Evidence strength can be classified as:

```text
LOW
MEDIUM
HIGH
```

This creates a more inspectable investigation process than asking an LLM to directly produce one final explanation.

---

### 📊 Deterministic Hypothesis Ranking

The LLM interprets evidence, but the final ranking is handled by application logic instead of allowing the model to invent arbitrary confidence percentages.

A simplified evidence contribution model uses:

```text
HIGH support           +3
MEDIUM support         +2
LOW support            +1

HIGH contradiction     -3
MEDIUM contradiction   -2
LOW contradiction      -1

NEUTRAL                 0
```

The ranking system can also account for evidence-source diversity.

A hypothesis supported independently by logs, source code, Git history, and documentation can therefore be treated differently from one supported only by several similar pieces of evidence from a single source.

The resulting score is an **evidence score**, not a probability that the hypothesis is true.

---

### 🧪 Active Hypothesis Verification

After hypotheses are generated and ranked, the strongest candidates can enter an active verification workflow.

For each selected hypothesis, the verification planner determines:

- What evidence should exist if the hypothesis is correct
- What evidence could contradict the hypothesis
- Which available investigation tool can test the requirement
- Whether further investigation is necessary

The agent can then perform targeted searches using the existing log, code, Git, and document tools.

New evidence is evaluated as:

```text
SUPPORTS
CONTRADICTS
NEUTRAL
```

Verification produces one of three outcomes:

```text
SUPPORTED
WEAKENED
INCONCLUSIVE
```

The hypotheses are then re-ranked using the newly collected evidence.

This allows the leading explanation to change when new supporting or contradictory evidence is discovered.

---

### ⚖️ Confirmation-Bias Protection

The verification workflow is designed to consider evidence that could **weaken** a hypothesis, not only evidence that confirms it.

The agent can reason about:

```text
What should be true if this hypothesis is correct?

What observation would contradict it?

Which tool can test that?
```

If required evidence is unavailable, the system preserves uncertainty rather than fabricating a result.

---

## 🏗️ Architecture

```text
┌───────────────────────────────────────────────────────────────┐
│                         React UI                              │
│       Dashboard • Incidents • Investigation Panel            │
│           Hypotheses • Verification Timeline                 │
└──────────────────────────────┬────────────────────────────────┘
                               │
                            REST API
                               │
                               ▼
┌───────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                         │
│                                                               │
│                  LangGraph Investigation                      │
│                          Agent                                │
│                            │                                  │
│              ┌─────────────┼─────────────┐                    │
│              │             │             │                    │
│              ▼             ▼             ▼                    │
│         Log Search     Code Search    Git Changes             │
│              │             │             │                    │
│              └─────────────┼─────────────┘                    │
│                            │                                  │
│                            ▼                                  │
│                     Docs / Runbook RAG                        │
│                            │                                  │
│                            ▼                                  │
│                       Evidence Store                          │
│                            │                                  │
│                            ▼                                  │
│                    Evidence Synthesis                         │
│                            │                                  │
│                            ▼                                  │
│                  Hypothesis Generation                        │
│                            │                                  │
│                            ▼                                  │
│                Evidence Mapping & Ranking                     │
│                            │                                  │
│                            ▼                                  │
│                 Active Verification Loop                      │
│                            │                                  │
│                            ▼                                  │
│                        Re-Ranking                             │
│                                                               │
│         SQLAlchemy + Alembic + PostgreSQL + pgvector          │
└───────────────────────────────────────────────────────────────┘
```

---

## 🔄 Investigation Workflow

The implemented investigation workflow is:

```text
Incident Created
       ↓
Investigation Initialized
       ↓
Investigation Planner
       ↓
Evidence Collection
   ├── Log Search
   ├── Code Search
   ├── Recent Git Changes
   └── Document / Runbook Search
       ↓
Evidence Persisted
       ↓
Evidence Synthesis
       ↓
Candidate Hypotheses Generated
       ↓
Evidence Mapped to Hypotheses
       ↓
Deterministic Ranking
       ↓
Top Hypotheses Selected
       ↓
Verification Planner
       ↓
Targeted Investigation
       ↓
New Evidence
       ↓
SUPPORTS / CONTRADICTS / NEUTRAL
       ↓
Verification Outcome
   ├── SUPPORTED
   ├── WEAKENED
   └── INCONCLUSIVE
       ↓
Hypothesis Re-Ranking
       ↓
Investigation Result Persisted
```

---

## 📁 Project Structure

```text
AI-Incident-Investigation-Agent/
│
├── backend/
│   ├── app/
│   │   │
│   │   ├── agents/
│   │   │   └── investigation/
│   │   │       ├── graph.py
│   │   │       ├── state.py
│   │   │       ├── llm.py
│   │   │       │
│   │   │       ├── nodes/
│   │   │       │   ├── planner.py
│   │   │       │   ├── execute_tool.py
│   │   │       │   ├── record_evidence.py
│   │   │       │   ├── synthesize_evidence.py
│   │   │       │   ├── generate_hypotheses.py
│   │   │       │   ├── map_evidence.py
│   │   │       │   ├── rank_hypotheses.py
│   │   │       │   ├── select_hypothesis_for_verification.py
│   │   │       │   ├── verification_planner.py
│   │   │       │   ├── evaluate_verification_evidence.py
│   │   │       │   ├── finalize_verification.py
│   │   │       │   └── finalize.py
│   │   │       │
│   │   │       └── prompts/
│   │   │
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── incidents.py
│   │   │       ├── investigations.py
│   │   │       ├── hypotheses.py
│   │   │       ├── verifications.py
│   │   │       ├── logs.py
│   │   │       ├── repositories.py
│   │   │       └── documents.py
│   │   │
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── core/
│   │   └── db/
│   │
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       │   ├── InvestigationPanel.tsx
│       │   ├── HypothesisCard.tsx
│       │   ├── HypothesisList.tsx
│       │   ├── LogsTab.tsx
│       │   ├── RepositoriesTab.tsx
│       │   └── DocumentsTab.tsx
│       │
│       ├── services/
│       └── types/
│
├── scripts/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

---

## 🗄️ Database Design

The system persists major investigation entities rather than keeping the workflow only in LLM context.

| Entity | Purpose |
|---|---|
| `Incident` | Production incident being investigated |
| `InvestigationRun` | Individual investigation execution |
| `InvestigationStep` | Persisted agent execution steps |
| `Evidence` | Evidence collected by investigation tools |
| `LogEntry` | Structured incident logs |
| `Repository` | Registered source repository |
| `SourceFile` / `CodeChunk` | Indexed source-code content |
| `Document` / `DocumentChunk` | Operational documents and RAG chunks |
| `Hypothesis` | Candidate incident explanation |
| `HypothesisEvidence` | Evidence-to-hypothesis relationships |
| `HypothesisVerification` | Verification run for a hypothesis |
| `VerificationStep` | Individual verification workflow steps |

Persistence enables:

- Investigation history
- Evidence provenance
- Agent execution timelines
- Hypothesis tracking
- Verification history
- Score updates
- Re-ranking
- UI state after page refresh

---

## 🖥️ Frontend

The React frontend provides an investigation-oriented interface with:

- Incident dashboard
- Incident creation and management
- Log inspection
- Repository association
- Document upload and indexing
- Investigation execution
- Investigation timeline
- Evidence cards
- Ranked hypothesis cards
- Supporting and contradicting evidence
- Manual hypothesis verification
- Verification outcomes
- Verification timeline
- Score changes and re-ranking

---

## 🚀 Quick Start

### Prerequisites

Make sure the following are installed:

- Docker Desktop
- Docker Compose
- Git
- Google AI API key

Docker Desktop must be running before starting the complete application.

### 1. Clone the Repository

```bash
git clone https://github.com/atul-kumar-30/AI-Incident-Investigation-Agent.git
cd AI-Incident-Investigation-Agent
```

### 2. Configure Environment Variables

Create a `.env` file from `.env.example`.

#### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

#### Linux / macOS

```bash
cp .env.example .env
```

Add the required API key and configuration values to `.env`.

> **Important:** Never commit API keys, credentials, or your real `.env` file to Git.

### 3. Start the Application

```bash
docker compose up -d --build
```

Docker Compose starts the required application services, including:

```text
PostgreSQL + pgvector
FastAPI Backend
React Frontend
```

### 4. Check Running Services

```bash
docker compose ps
```

### 5. View Container Logs

```bash
docker compose logs -f
```

### 6. Stop the Application

```bash
docker compose down
```

Avoid:

```bash
docker compose down -v
```

unless you intentionally want to remove persisted Docker volumes and local database data.

---

## 💻 Local Development

### Backend

```bash
cd backend
python -m venv venv
```

Activate the environment.

#### Windows

```powershell
.\venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
alembic upgrade head
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Create a production build:

```bash
npm run build
```

---

## 🧪 Testing

The backend test suite uses deterministic/mock LLM behavior for normal automated tests so the suite does not depend on external model availability or API rate limits.

Run the test suite with:

```bash
cd backend
pytest tests/ -v
```

### PostgreSQL Integration Testing

PostgreSQL-specific integration tests use **Testcontainers** to validate behavior against a real PostgreSQL environment.

This is important because SQLite and PostgreSQL can differ in areas such as:

- PostgreSQL enums
- JSON / JSONB
- PostgreSQL-specific data types
- Foreign-key behavior
- Alembic migrations
- pgvector

Real-model integration tests can be executed separately when a valid API key is available.

---

## 🛡️ Reliability & Guardrails

The project includes several controls to make the agent workflow more predictable and auditable.

### Bounded Agent Loops

Investigation and verification workflows use maximum iteration limits and tool budgets.

### Duplicate Query Prevention

Repeated identical tool calls can be blocked while allowing refined searches with different inputs.

### Evidence Provenance

Evidence retains source information rather than becoming anonymous LLM context.

### Evidence Validation

Evidence references are validated before hypothesis mappings are persisted.

### Deterministic Ranking

The LLM interprets evidence, while application logic handles the final scoring and ranking.

### Contradiction Seeking

Verification considers evidence that could weaken the current hypothesis instead of searching only for confirmation.

### Explicit Uncertainty

Unavailable or insufficient evidence can result in:

```text
INCONCLUSIVE
```

rather than a fabricated conclusion.

---

## 🧠 Why LangGraph?

This project requires more than a linear RAG chain.

The investigation agent must maintain state and repeatedly decide what action should happen next:

```text
Plan
 ↓
Search Logs
 ↓
Observe
 ↓
Search Code
 ↓
Observe
 ↓
Inspect Git
 ↓
Observe
 ↓
Search Documents
 ↓
Generate Hypotheses
 ↓
Verify Hypothesis
 ↓
Search Again
 ↓
Re-Evaluate
```

LangGraph provides the stateful orchestration, conditional routing, iterative execution, and controlled termination required for this workflow.

---

## 📚 Why RAG?

Source code and runtime logs cannot always explain operational behavior.

Runbooks and architecture documentation may contain:

- Known failure patterns
- Operational constraints
- Troubleshooting procedures
- Architecture context
- Recovery guidance

The document retrieval system uses RAG to retrieve relevant operational knowledge when it is needed instead of placing entire documents into every LLM request.

---

## 🔍 Why Hybrid Retrieval?

Technical incidents frequently contain exact identifiers such as:

```text
/login
HTTP 500
AuthService
connection_timeout
pool_size
```

Lexical retrieval is useful for exact technical identifiers.

Semantic retrieval is useful when a query and a document describe the same concept using different wording.

The document retrieval layer combines both approaches to improve retrieval relevance.

---

## 📌 Current Scope

The current implementation covers the investigation workflow through **active hypothesis verification and re-ranking**.

The project focuses on **investigation and evidence-grounded reasoning**, not autonomous remediation.

The system does **not automatically**:

- Modify production systems
- Apply code patches
- Change infrastructure configuration
- Execute rollbacks
- Create pull requests
- Perform destructive production actions
- Claim absolute causal certainty from incomplete evidence

Some verification requirements may remain unavailable when they require external systems that are not currently integrated, such as infrastructure metrics or distributed traces.

---

## 🗺️ Development Milestones

The project was developed incrementally through seven major milestones:

1. **Application Foundation** — FastAPI, React, PostgreSQL, Docker, and incident management.
2. **Agent Architecture** — LangGraph orchestration, planner, tool registry, investigation persistence, and evidence storage.
3. **Log Investigation** — Structured log ingestion, log search, and iterative evidence collection.
4. **Code & Git Investigation** — Deterministic source-code search and recent Git-change retrieval.
5. **Document RAG** — Document ingestion, embeddings, pgvector, lexical search, semantic search, and hybrid retrieval.
6. **Evidence-Grounded Hypotheses** — Evidence synthesis, hypothesis generation, evidence mapping, and deterministic ranking.
7. **Active Verification** — Targeted hypothesis testing, contradiction seeking, verification outcomes, score updates, and re-ranking.

---

## 🎯 What This Project Demonstrates

This project demonstrates practical experience with:

- Agentic AI architecture
- LangGraph stateful workflows
- LangChain
- LLM structured output
- Tool calling
- Retrieval-Augmented Generation (RAG)
- Embeddings
- Vector databases
- Semantic and lexical retrieval
- Hybrid retrieval
- Multi-source evidence collection
- Evidence provenance
- Hypothesis generation
- Hypothesis verification
- Confirmation-bias mitigation
- Deterministic scoring and ranking
- FastAPI backend architecture
- React + TypeScript frontend development
- PostgreSQL + pgvector
- SQLAlchemy + Alembic
- Docker + Docker Compose
- Automated testing
- PostgreSQL integration testing with Testcontainers

---

## ⚠️ Limitations

- Investigation quality depends on the evidence available to the system.
- LLM interpretation can still be imperfect.
- Direct integrations with systems such as Prometheus, distributed tracing platforms, Kubernetes telemetry, and cloud monitoring are outside the current scope.
- A `SUPPORTED` hypothesis means that currently available evidence strengthened that explanation; it does not represent absolute proof of causality.
- The system intentionally avoids autonomous remediation.

---

## 🔮 Future Possibilities

Potential extensions include:

- Infrastructure metrics retrieval
- Distributed trace analysis
- Kubernetes investigation
- Incident-history retrieval
- Additional observability integrations
- Human-reviewed root-cause analysis reports
- Remediation recommendations
- Approval-gated remediation workflows

These are optional future extensions and are **not required for the current investigation system**.

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.