# Inevitable — Phase 10: Security and Reliability Audit Report

As the acting security engineer, I have completed a comprehensive review of the Inevitable repository. I evaluated the platform against realistic adversarial attack vectors that a publicly exposed verification agent would face. 

This document outlines the findings, the fixes I have implemented in this phase, and the residual risks that remain.

## 1. Resolved Vulnerabilities (Fixed in Phase 10)

### 1.1. Server-Side Request Forgery (SSRF) and Internal Network Probing (High)
**Vulnerability:** While `validate_repository_url` correctly checked for `localhost`, an attacker could bypass this by providing IP addresses within internal subnets (e.g., `10.0.x.x`, `192.168.x.x`), allowing them to use the `RepositoryInspector` git clone logic to probe internal infrastructure or hit cloud metadata endpoints (like AWS/GCP `169.254.169.254`).
**Fix Applied:** Added `ipaddress` parsing to `validate_repository_url`. It now explicitly rejects any hostname that resolves to `is_private`, `is_loopback`, or `is_link_local`, as well as strictly blocking `metadata.google.internal`. (Verified by tests).

### 1.2. Secret Leakage via Environment Inheritance (Critical)
**Vulnerability:** In `PytestRunner`, the execution command passed `os.environ` entirely to the untrusted pytest environment:
```python
env={**os.environ, "PYTHONPATH": str(working_dir)}
```
If a malicious repository included a backdoor in a `pytest` plugin or `conftest.py`, the code would have access to the host's `TOGETHER_API_KEY` and other sensitive environment data, allowing exfiltration.
**Fix Applied:** Implemented a strict allowlist for environment inheritance (`PATH`, `LANG`, `LC_ALL`, `USER`, `HOME`). Secrets are now stripped from the subprocess context before untrusted code execution.

### 1.3. Cross-Request Data Leakage / Global State Mutation (High)
**Vulnerability:** To enable the safe `demo:local-fixture` bypass, `api/v1.py` mutated the global `settings` object:
```python
settings.enable_untrusted_execution = True
```
This created a severe race condition in an asynchronous environment. If a judge triggered the demo route while an attacker submitted a malicious external repo, the attacker's execution would be improperly permitted due to the shared global setting.
**Fix Applied:** Removed global mutation entirely. Refactored `PatchEvaluator` and `PytestRunner` to accept an explicit `is_safe_fixture: bool` localized variable tied directly to the request scope. 

### 1.4. Orphaned Process Exhaustion (Medium)
**Vulnerability:** The timeout mechanism for untrusted execution called `process.kill()`, which sent `SIGKILL` to the pytest parent process. However, if the malicious test spawned its own child processes (e.g., launching background workers), those processes would be orphaned, slowly exhausting host PIDs and memory.
**Fix Applied:** Refactored `PytestRunner` to spawn execution with `preexec_fn=os.setsid` and kill the entire process group (`os.killpg`) upon timeout, guaranteeing a clean termination tree.

---

## 2. Validated Security Boundaries (Confirmed Safe)

- **Path Traversal & Symlink Attacks:** Confirmed that `RepositoryInspector.is_safe_path()` successfully neutralizes symlinks bypassing the sandbox via `resolve().relative_to()`.
- **Patch Format Integrity:** Confirmed `validate_patch` actively denies path traversal (`../`) and absolute paths (`/etc/..`) in unified diffs.
- **Git Argument Injection:** Confirmed that URL parsing strictly requiring `https://` blocks `ext::` execution and `-` options, successfully neutralizing argument injection in `Repo.clone_from()`.
- **Frontend XSS:** Confirmed that React's native node rendering (e.g. `{ev.snippet}`) inherently sanitizes source evidence snippets and patch outputs, preventing DOM-based XSS when reviewing malicious repositories.
- **State Machine Manipulation:** Confirmed that `determine_verification_status` calculates conclusions exclusively from deterministic Python subprocess `exit_codes`, ensuring AI halucination cannot invent a "VERIFIED" status.

---

## 3. Residual Risks and Unresolved Limitations (Documented)

While high-severity risks have been neutralized, the following limitations remain by design for this hackathon context:

1. **Host-level Sandboxing:** The execution layer runs processes under the host user. It utilizes bounded timeouts and truncates output, but it does not employ Linux `cgroups`, `seccomp`, or unprivileged `namespaces` (Docker). Because of this, `ENABLE_UNTRUSTED_EXECUTION=true` remains heavily restricted.
2. **Denial of Service (Memory):** A malicious script could rapidly allocate RAM to cause an Out-Of-Memory (OOM) kill before the time limit expires. True `prlimit` or `ulimit -v` enforcement is not natively achievable cross-platform in pure asyncio without system wrappers.
3. **Network Exfiltration:** The untrusted pytest environment retains outbound network access. While secrets have been stripped, the executed code can still ping external tracking servers.

## Conclusion

The system relies on the `BLOCKED` status capability to prevent arbitrary execution outside the verified `demo:local-fixture`. This strikes the correct balance of safety and demonstration functionality for Phase 10 without falsely claiming isolation certification.

All full-system integration tests and checks pass. Hardening complete.
