# Inevitable — Development Roadmap

Inevitable is being developed across **12 sequential phases**. The implementation must strictly follow this order. Each phase must be completed and tested before the next phase begins.

## Phase 1: Foundation and project identity
**Goal:** Establish the project structure, documentation, and core identity.
- Monorepo structure (`frontend/`, `backend/`, `docs/`)
- `README.md`, `CLAUDE.md`, `docs/architecture.md`, `docs/roadmap.md`
- License and basic ignore rules

## Phase 2: Backend foundation
**Goal:** Create the baseline Python service.
- FastAPI setup and configuration
- Pydantic schemas
- Health and information endpoints
- Logging, CORS, and error handling
- Automated tests for the foundation

## Phase 3: Real Gemma 4 integration
**Goal:** Connect to the Gemma 4 AI model.
- Verify model access method and provider abstraction
- Validate structured model outputs with Pydantic
- Handle timeouts, retries, and provider failures
- Clear distinction between mocked and real integration tests

## Phase 4: Repository investigation
**Goal:** Safely inspect and collect evidence from Python repositories.
- Bounded repository cloning and Git revision recording
- Source search and Python AST parsing
- Collection of source evidence (paths, line ranges, snippets)
- Protection against SSRF, path traversal, and sensitive file access

## Phase 5: Test-execution harness
**Goal:** Controlled execution of tests to verify patches.
- Subprocess execution adapter for pytest
- Resource limits (CPU, memory, time) if supported
- Capture of execution results (stdout/stderr, exit codes)
- **Note:** Strict sandbox is only claimed if genuinely isolated; otherwise, restricted to a demo repository.

## Phase 6: Patch and regression-test generation
**Goal:** Generate and safely apply AI-proposed fixes.
- Candidate unified diffs and regression tests via Gemma 4
- Validation of patch paths and scope
- Apply patches in a disposable worktree
- Capture baseline and patched execution results

## Phase 7: Proof-Carrying Patches
**Goal:** Deterministic verification and evidence bundling.
- Deterministic verification state machine (VERIFIED, REJECTED, INCONCLUSIVE, BLOCKED)
- Cryptographic hashing (SHA-256) of sources and patches
- JSON and Markdown report generation
- Distinction between AI explanations and trusted execution facts

## Phase 8: Frontend
**Goal:** Build the React/Vite user interface.
- Inevitable branding and dark graphite aesthetic
- Repository URL and defect inputs
- Evidence viewer, patch viewer, and test results presentation
- Downloadable reports and clear state indicators

## Phase 9: End-to-end integration
**Goal:** Connect all components for a complete workflow.
- Full API integration between frontend and backend
- Demonstrate workflow on a controlled sample repository containing a known defect
- Verify entire chain from input to Proof-Carrying Patch

## Phase 10: Security and reliability
**Goal:** Final review and hardening.
- URL handling and SSRF prevention
- Prompt injection defenses
- Path traversal and subprocess safety review
- Report integrity checks and documentation of residual risks

## Phase 11: Deployment readiness
**Goal:** Prepare for production deployment.
- DigitalOcean configuration (if applicable and approved)
- Docker support for reproducibility
- Health checks and deployment documentation

## Phase 12: Hackathon polish and submission
**Goal:** Finalize the project for Hacktoberfest.
- Run all tests and builds
- Verify setup instructions and license
- Prepare genuine screenshots and a concise demo script
- Honestly report completed features and limitations
