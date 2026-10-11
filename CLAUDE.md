# Inevitable — Engineering Guide

## What is Inevitable?

Inevitable is an AI-powered software verification agent that provides **Proof-Carrying Patches** for AI-generated code fixes. The core philosophy: "Don't trust the patch. Prove it."

## Project Structure

This is a monorepo with the following structure:

```
inevitable/
├── apps/
│   └── web/              # React + Vite frontend dashboard
├── packages/
│   └── backend/          # FastAPI Python backend service
├── .github/              # GitHub workflows and templates
├── docs/                 # Documentation (when Phase 4+)
├── tests/                # Shared E2E tests (when Phase 9+)
├── scripts/              # Build/setup scripts
├── .claude/              # Claude-specific configuration
│   └── agents/           # Specialized agent definitions
│   └── memory/           # Persistent memory files
├── .gitignore
├── README.md
├── pyproject.toml        # Python build system
├── package.json          # Node.js dependencies
└── tsconfig.json         # TypeScript configuration
```

## Engineering Principles

### Phase Discipline (MUST FOLLOW)

**Complete only one phase at a time.** Never skip or combine phases.

The 12-phase roadmap is:
1. **Foundation and project identity** — Current phase
2. **Backend foundation** — FastAPI, schemas, health endpoints
3. **Real Gemma 4 integration** — Model provider abstraction
4. **Repository investigation** — Safe source inspection
5. **Test-execution harness** — Controlled pytest execution
6. **Patch and regression-test generation** — Diff generation
7. **Proof-Carrying Patches** — Evidence, hashes, reports
8. **Frontend** — React dashboard
9. **End-to-end integration** — Full workflow demo
10. **Security and reliability** — SSRF, injection, sandbox review
11. **Deployment readiness** — DigitalOcean prep
12. **Hackathon polish** — Final submission

**Stop after each phase and wait for explicit approval.**

### Security-First Mindset

Treat ALL external inputs as untrusted:
- Repository URLs (validate protocol, reject credentials)
- Source files (collect only relevant evidence, exclude secrets)
- AI model outputs (validate structured responses)
- User input (sanitize paths, limit sizes)
- Patches (validate unified diff format, reject path traversal)

### Code Quality Standards

**Python Backend:**
- Use `ruff` for linting (config in pyproject.toml)
- Type hints everywhere
- Pydantic models for all API schemas
- Deterministic logic for security decisions
- Clear separation: API → Config → Repo inspection → AI → Verification → Reporting

**React Frontend:**
- TypeScript with strict mode
- Maintainable component architecture
- Accessible, responsive UI
- Real backend data (demo fixtures must be clearly labeled)

### Honesty Principle

- Never fabricate verification states, test results, or hashes
- Clearly label mocked/unavailable features
- Distinguish model-generated content from trusted execution metadata
- Document known limitations and blocked capabilities

## Phase 1: Foundation & Identity

### This phase completes:
- [x] Monorepo structure (package.json, pyproject.toml, tsconfig.json)
- [x] CLAUDE.md with project identity
- [x] README.md for users
- [x] Architecture documentation
- [x] Apache-2.0 license file
- [x] .env.example template
- [ ] CI workflow templates
- [x] Roadmap/implementation guide

### Deliverables Checklist:
When Phase 1 is complete, you should have:
```
inevitable/
├── .github/
│   ├── workflows/
│   │   └── ci.yml         # Basic CI for backend tests
│   └── PULL_REQUEST_TEMPLATE.md
├── CLAUDE.md              # Completed - project identity and rules
├── LICENSE                # Apache-2.0 text
├── README.md              # User-facing documentation
├── docs/
│   ├── architecture.md    # System design overview
│   └── ROADMAP.md         # Implementation phases
├── .env.example           # Environment template
└── ... (package.json, pyproject.toml already created)
```

## Important Reminders

- **Never implement Phase 2 without explicit approval**
- If a dependency or prerequisite is unavailable, report it — don't fake success
- Security decisions must be deterministic and well-documented
- This is for Hacktoberfest — focus on a working demo over breadth
