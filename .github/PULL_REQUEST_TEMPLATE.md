# Inevitable — Pull Request Template

**Thank you for contributing to Inevitable!** Before submitting your PR, please complete the checklist below.

---

## Security & Safety Checklist ⚠️

Inevitable handles untrusted inputs (repository URLs, code). Verify:

- [ ] No hardcoded secrets or credentials in the code
- [ ] No private API keys exposed
- [ ] Any security-sensitive changes have been reviewed
- [ ] No path traversal vulnerabilities introduced
- [ ] Execution sandboxing remains intact (if applicable)

---

## Testing Checklist ✅

- [ ] All backend tests pass (`pytest tests/`)
- [ ] All frontend tests pass (if applicable)
- [ ] The CI pipeline passes on this branch
- [ ] No new warnings in linting output (ruff, oxlint, mypy)

---

## Implementation Details

**Describe what your changes do and why:**

```
<!-- Provide a clear, concise description of the changes -->
```

**Relevant issue number (if applicable):**

```
<!-- Example: Fixes #123 -->
```

---

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 🎨 Code style/quality improvement (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🔒 Security enhancement
- [ ] 📝 Documentation update
- [ ] 🔄 Refactoring (code structure changes without behavior changes)
- [ ] ⚠️ Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 🧪 Tests only

---

## Testing Performed

**How did you test these changes?**

```
<!-- Describe manual testing, edge cases covered, and any known limitations -->
```

---

## Code Review Notes

**Any specific areas reviewers should focus on:**

```
<!-- Highlight complex logic, security-sensitive code, or architectural decisions -->
```

---

## Related Documentation

- [x] Self-reviewed (basic documentation updated)
- [ ] Added/updated inline code comments where needed
- [ ] Updated README.md if necessary
- [ ] Updated docs/architecture.md if architecture changed

---

### 🤖 Generated with [Claude Code](https://claude.com/claude-code)
