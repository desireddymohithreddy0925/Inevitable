# Inevitable Architecture

## System Overview

Inevitable is a monolithic FastAPI service with a separate React frontend. The system implements a **Proof-Carrying Patch** workflow where AI-generated code changes are accompanied by reproducible verification evidence.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              React + Vite Frontend (frontend)                         │  │
│  │  - Repository URL input                                               │  │
│  │  - Defect description input                                           │  │
│  │  - Investigation timeline                                            │  │
│  │  - Evidence viewer                                                    │  │
│  │  - Patch viewer with diff                                            │  │
│  │  - Test results (baseline vs patched)                                 │  │
│  │  - Verification state indicator                                      │  │
│  │  - Report download (JSON/Markdown)                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ HTTP/JSON (port 8000)
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND SERVICE                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     FastAPI Application                                │  │
│  │                                                                       │  │
│  │  ┌─────────────┐    ┌──────────────┐    ┌────────────────────┐     │  │
│  │  │ API Layer   │    │ Validation   │    │ Error Handling      │     │  │
│  │  │ (routes)    │───▶│ (Pydantic)   │───▶│ (structured)        │     │  │
│  │  └─────────────┘    └──────────────┘    └────────────────────┘     │  │
│  │                           │                                         │  │
│  │                           ▼                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │                    Core Engine                                 │   │  │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌────────────────────┐     │   │  │
│  │  │  │ Repo        │ │ AI Analysis │ │ Test Execution     │     │   │  │
│  │  │  │ Inspector   │ │ (Gemma 4)   │ │ Harness            │     │   │  │
│  │  │  └─────────────┘ └─────────────┘ └────────────────────┘     │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  │                           │                                         │  │
│  │                           ▼                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │                 Verification Policy                            │   │  │
│  │  │  (Deterministic state machine, rules-based verdicts)          │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  │                           │                                         │  │
│  │                           ▼                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │                Evidence & Report Generator                     │   │  │
│  │  │  - Source hashes (SHA-256)                                     │   │  │
│  │  │  - Patch application logs                                      │   │  │
│  │  │  - Test execution metadata                                     │   │  │
│  │  │  - JSON/Markdown report generation                            │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘
│                              │
│              ┌────────────────┴────────────────┐
│              ▼                                  ▼
│  ┌─────────────────────┐            ┌──────────────────────┐
│  │ GitPython           │            │ Subprocess           │
│  │ - Repository clone  │            │ Execution (pytest)   │
│  │ - Source retrieval  │            │ with resource limits │
│  │ - Patch application │            └──────────────────────┘
│  └─────────────────────┘
│              │                                  │
└──────────────┼──────────────────────────────────┼──────────────────┐
               │                                  │                   │
               ▼                                  ▼                   │
    ┌──────────────────────┐           ┌─────────────────┐          │
    │  HTTPX Client        │           │ SQLite (opt)    │          │
    │  - GEMMA 4 via       │           │ - Session data  │          │
    │    provider (API)    │◄──────────►│                 │          │
    └──────────────────────┘           └─────────────────┘          │
                                                                     ▼
                                                                  External
                                                                 Repositories
```

## Core Components

### 1. API Layer (`backend/inevitable/api`)

RESTful endpoints for the frontend and CLI:

- `GET /health` - Health check
- `POST /api/v1/investigate` - Start investigation
- `GET /api/v1/investigations/{id}` - Get progress
- `GET /api/v1/results/{id}` - Get final report

### 2. Validation Layer (`backend/inevitable/validation`)

Pydantic schemas enforce strict input/output contracts:

- Request bodies (repository URL, defect description)
- Structured model responses
- Verification state transitions
- Evidence metadata

### 3. Repository Inspector (`backend/inevitable/repo`)

Bounded, safe inspection of Python repositories:

- Validates URL scheme (HTTPS only, no credentials)
- Clones to isolated temp directory
- Collects source evidence with line ranges
- Excludes sensitive files (`.env`, `__pycache__`, binaries)
- Records exact Git revision

### 4. AI Analysis (`backend/inevitable/ai`)

Gemma 4 integration with provider abstraction:

- Supports multiple providers (HuggingFace, Together.ai, etc.)
- Validates structured JSON outputs against schema
- Handles timeouts and retries
- **Security**: Treats repo content as data, not instructions; defends against prompt injection

### 5. Test Execution Harness (`backend/inevitable/test_runner`)

Controlled pytest execution:

- Spawns subprocesses with resource limits (CPU, memory, time)
- Captures stdout/stderr and exit codes
- Returns actual test results (not mocked)
- **Note**: No true sandbox — only resource limits for the controlled demo repository

### 6. Verification Policy (`backend/inevitable/policy`)

Deterministic state machine that calculates verification status:

```
State transition rules (AI never decides, policy decides):
┌─────────┐    ┌───────────────┐    ┌──────────┐
│ BLOCKED │    │  REJECTED     │    │ VERIFIED │
└─────────┘    └───────────────┘    └──────────┘
     ▲              ▲                    ▲
     │              │                    │
No   │  Required   │  Test failed       │ Both baseline and patched tests pass
safe │  test(s)    │  (with patch      │ Intentionally failing test passes
to   │  missing    │  applied)         │ or both fail with expected result
     │  (or        │                   │
  AI │  policy     │                   │
 says "│  restriction│                   │
 can't│  ")        │                   │
 proceed│          │                   │
       │          └───────────┘
       │                   No reliable evidence
       │                   of fix efficacy

INCONCLUSIVE: Evidence insufficient, ambiguous, or contradictory
```

### 7. Evidence & Report Generator (`backend/inevitable/reporting`)

Produces machine-readable and human-readable outputs:

- **JSON report**: Structured verification data
- **Markdown report**: Formatted for human reading
- **Patch hash**: SHA-256 of unified diff
- **Source hashes**: File content hashes for integrity verification

## Security Architecture

### 1. URL Validation

```python
# Reject protocols: file://, git://, http:// (no credentials)
# Accept: https:// only
# Reject embedded credentials: user:pass@github.com
```

### 2. Source File Filtering

Exclude:
- Secrets (`.env`, files matching secret patterns)
- Generated files (`__pycache__`, `.pyc`, `build/`)
- Large binaries
- Irrelevant directories (`.git`, node_modules, vendor/)

Include:
- Python source files
- Test files
- Relevant configuration (if small and safe)

### 3. Patch Validation

```python
# Reject path traversal: ../../../etc/passwd
# Reject absolute paths: /home/user/project/...
# Limit file scope: max 5 changed files, max 200 lines total
# Validate unified diff format
```

### 4. Execution Limits

```python
CPU_LIMIT = 0.2    # 20% of one core
MEMORY_LIMIT = "512MB"
TIMEOUT = 30        # seconds per test run
```

### 5. Prompt Injection Defense

- AI receives repo content as **data**, not system prompt
- Structured output validation prevents injection effects
- Critical decisions made by deterministic policy, not model

## Repository and Workflow

### Demo Repository (`backend/demo_repo/`)

A controlled Python package with:
- Known defect (pre-programmed bug)
- Reproduction test case
- Documented expected behavior

This ensures reproducible verification during demo runs.

### Full Repository Investigation Flow

1. **Input validation**: URL, defect description
2. **Repository clone**: To isolated worktree/temp directory
3. **Source inspection**: Collect evidence from relevant files
4. **AI analysis**: Gemma 4 proposes fix and test
5. **Baseline execution**: Run tests on original code
6. **Patch application**: Apply diff to disposable copy
7. **Patched execution**: Run tests on patched code
8. **Verification**: Apply policy rules, determine state
9. **Report generation**: JSON + Markdown with all evidence

## Verification States

| State | Description | Trigger |
|-------|-------------|---------|
| `VERIFIED` | Evidence shows fix works | Baseline fails, patched passes expected test |
| `REJECTED` | Fix does not work | Required test fails after patch applied |
| `INCONCLUSIVE` | Insufficient evidence | Tests skipped, ambiguous results |
| `BLOCKED` | Cannot proceed safely | Security policy, missing prerequisites |

## File Organization

```
backend/inevitable/
├── __init__.py
├── api/                # FastAPI routes
│   ├── __init__.py
│   └── v1.py          # API endpoints
├── ai/                 # Gemma 4 integration
│   ├── __init__.py
│   ├── provider.py    # Provider abstraction
│   └── gemma.py       # Gemma 4 specific implementation
├── repo/               # Repository inspection
│   ├── __init__.py
│   ├── inspector.py   # Source collection
│   └── validator.py   # Security validation
├── test_runner/        # Test execution harness
│   ├── __init__.py
│   ├── runner.py      # Pytest execution
│   └── limits.py      # Resource constraints
├── policy/             # Verification state machine
│   ├── __init__.py
│   └── verifier.py    # Deterministic verdict logic
├── reporting/          # Evidence and reports
│   ├── __init__.py
│   ├── evidence.py    # Evidence collection
│   └── report.py      # JSON/Markdown generation
├── config.py           # Configuration management
├── schemas.py          # Pydantic models
└── app.py              # FastAPI application factory
```

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Backend | Python + FastAPI | Python-native, async support, rapid dev |
| Validation | Pydantic v2 | Type safety, validation, docs |
| Git operations | GitPython | Standard library integration |
| Test runner | pytest | Standard Python testing |
| Subprocess limits | resource+psutil | CPU, memory, time constraints |
| HTTP client | httpx | Async support, timeouts |
| Frontend | React + Vite | Familiar, fast dev server |
| Language | TypeScript | Type safety, ecosystem |
| Styling | Tailwind CSS (planned) | Utility-first, maintainable |

## Known Limitations (Phase 1 baseline)

- **No sandbox**: Subprocess execution has only resource limits, not true isolation
- **Single language**: Python/pytest only in initial scope
- **Demo repo**: Controlled repository ensures reproducibility
- **No GitHub integration**: Manual repo URL input only
- **Sequential phases**: Full multi-agent orchestration deferred
