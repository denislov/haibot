---
phase: 01
slug: rich-media-and-external-cli-chat-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + frontend build/manual verification |
| **Config file** | `pyproject.toml` / `frontend/package.json` |
| **Quick run command** | `pytest tests/unit/providers tests/unit/workspace tests/unit/cli -q` |
| **Full suite command** | `python scripts/run_tests.py -a && (cd frontend && pnpm build)` |
| **Estimated runtime** | ~180 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/providers tests/unit/workspace tests/unit/cli -q`
- **After every plan wave:** Run `python scripts/run_tests.py -a && (cd frontend && pnpm build)`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | MSG-01/MSG-02/MSG-03 | unit | `pytest tests/unit/workspace -q` | ✅ | ⬜ pending |
| 01-01-02 | 01 | 1 | MSG-01/MSG-02 | unit | `pytest tests/unit/providers -q` | ✅ | ⬜ pending |
| 01-02-01 | 02 | 2 | CLI-01/CLI-02/CLI-03 | unit | `pytest tests/unit/cli -q` | ✅ | ⬜ pending |
| 01-02-02 | 02 | 2 | CLI-04/CLI-05/SAFE-01/SAFE-02/SAFE-03 | integration | `python scripts/run_tests.py -a` | ✅ | ⬜ pending |
| 01-03-01 | 03 | 2 | RICH-01/RICH-02/RICH-03/RICH-04 | build | `cd frontend && pnpm build` | ✅ | ⬜ pending |
| 01-03-02 | 03 | 2 | MSG-03/CLI-04/CLI-05 | manual + build | `cd frontend && pnpm build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Existing infrastructure covers Python unit and integration checks.
- [ ] Frontend build dependency availability in `frontend/` must be confirmed
  before executing UI work.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Image/audio/video blocks render correctly in chat | RICH-01/RICH-02/RICH-03/RICH-04 | Visual playback and layout behavior are UI-specific | Open the chat UI, send or replay messages containing each block type, verify inline rendering and ordering |
| CLI transcript streams coherently during live execution | CLI-04/CLI-05 | Live UX and transcript pacing cannot be validated by static grep alone | Trigger each CLI tool from chat and confirm transcript/progress updates appear without freezing the conversation |
| Reconnect/history replay reproduces visible output | MSG-02/MSG-03/CLI-05 | Requires browser refresh/reconnect behavior | Start a run, refresh or reconnect, then verify transcript/media blocks are still visible and ordered correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all missing references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
