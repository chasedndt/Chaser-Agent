# 2026-09-27 — Talk-next HUD visual QA and narrow reflow

## Repo-truth delta

The Talk-next sequence had deterministic tests but no screenshot of the actual native Tk HUD. A synthetic no-device capture at 280 px showed clipped phase/action text and truncated Resume, Take over and Cancel reply labels. At 410 px, the voice flow was understandable but both disabled buttons read "Stopping…" during a queued next take.

## Changes

- Wrap phase, action, session, notice, voice-status and draft labels to the actual canvas width.
- Below 340 px, rearrange the four computer-use controls to a 2×2 grid and the three voice controls to two rows. Keep the normal four-across/three-across layout above that threshold.
- During Talk-next cancellation, label disabled controls "Talk queued" and "Stopping reply" so the next action and current work are distinct.
- Add a fake-widget regression test for 280/410 px layout positions and dynamic text wrapping.

## Visual evidence

The [self-contained visual audit](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-talk-next-hud/QA.md>) contains numbered actual-Tk screenshots. The first high-DPI cropped captures were rejected and replaced before judging the UI. The accepted narrow before/after pair shows clipping removed at the tested width. The capture used a fake token, fake voice controller and inert speech worker; no service, model, microphone or speaker started.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_hud.py tests/test_voice_ack.py tests/test_local_audio.py tests/test_local_voice.py tests/test_desktop_voice.py` — **51 passed**.
- Same five files in the optional E: speech virtual environment — **51 passed**.
- `PYTHONPATH=src python -m pytest -q` — **326 passed, 1 skipped, 31 subtests passed, 1 failed** in 48.72s. The sole failure remains the locked canon-core manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes; its manifest says 1489. Neither file was edited.
- `git diff --check` — passed, with only line-ending warnings from Git.

## Boundaries and remaining work

The visual QA covers only the tested native window widths/states and synthetic inputs. It does not prove keyboard order, screen-reader labels, contrast against a formal criterion, all scaling combinations, acoustic feedback, real cancellation latency or operator microphone acceptance. The current E: runtime still fails the private-ACL preflight, and no real computer-use executor or general conversational provider is connected. The full HTTP/HUD/voice goal stays active.
