# Chaser Agent: setup and onboarding

12 November 2026. Chaser gets a first-run walk-through and one short command, `chaser`, in the terminal and in the HUD. Chase asked for this on 11 November 2026: an easy panel to add and configure a Cloud key, a pre-flight check, a shortcuts panel, a simple command such as `chaser gateway`, and onboarding similar to OpenClaw's and Hermes'.

## Moat check

| Question | Answer |
|---|---|
| Could an agent rebuild it quickly? | Yes. A setup wizard, a key panel and a start command are a day's work for Claude Code or Codex. |
| Is there already a free or cheaper tool? | For their own agents, yes. OpenClaw has `openclaw onboard` (QuickStart or Advanced), `configure` and `doctor`. Hermes has `hermes setup`, `gateway` and `doctor --fix`. Neither sets up Chaser. |
| What stays hard to replace? | Nothing in the setup itself. It's table stakes: without it nobody but Chase can start Chaser. Its value is getting someone to their first receipted, approved task quickly. |
| Verdict | **Build it small, from the pieces Chaser already has.** It reuses the existing service, token, ACL check, HUD and key file. The one part that adds to the moat is the reviewer name: approvals from the HUD are now signed by a named person instead of `local_operator`. |

## The command

| Command | What it does |
|---|---|
| `chaser` | Shows what's set up and what to run next. Offers onboarding if it hasn't run. |
| `chaser onboard` | First run, in six steps: check this computer, create the private data folder, add a ChaseOS Cloud key (optional), your name on approvals, the stop shortcuts, start Chaser and open the HUD. **QuickStart** asks only for the key and the name; **Advanced** also asks for the folder, port and packs. `--non-interactive` takes flags and asks nothing; `--reset` starts from default settings but keeps work, receipts and the key. |
| `chaser gateway` | Starts Chaser's service in the background and waits until it answers. `stop`, `restart`, `status` (routes and sessions) and `logs`. `--foreground` runs it in the terminal; `--open` opens the HUD. `stop` also finds a service started by `Start-ChaserAgent.ps1`. |
| `chaser setup` | A numbered menu for every setting: key, folder and port, name, packs, shortcuts, checks, start or stop. `chaser setup key` jumps to one section. |
| `chaser doctor` | Pre-flight checks. `--online` also asks ChaseOS Cloud for the key's balance, which costs nothing; `--fix` creates the private data folder; `--json` for scripts. |
| `chaser key` | `status`, `add` (pasted with no echo), `check` and `remove`. If Chaser is running, it uses a new key at once. |
| `chaser shortcuts` | Shows the stop and take-over keys and whether each is free. `set stop Ctrl+Alt+Shift+X`, or `reset`. |
| `chaser ask`, `open`, `decide`, `agent-status` | The existing commands, using the folder and port from settings, so they need no flags. |

`python -m chaser_agent …` runs the same command before the package is reinstalled with the new `chaser` entry point.

## The HUD

- **Settings** in the foot of the panel opens four tabs: **Cloud key**, **Your name**, **Shortcuts** and **Checks**. Settings covers the panel only, so the pill and Stop stay visible.
- **First run:** until onboarding is finished, the empty panel shows a "Welcome to Chaser" card. **Set up Chaser** walks the same four tabs as steps (Step 1 of 4, Back, Next, Finish).
- **Cloud key:** a password field. The key is checked with ChaseOS Cloud's balance endpoint, saved encrypted for this Windows account, used from the next step on with no restart, and never sent back to the page. A key ChaseOS Cloud refuses isn't saved. Remove asks twice.
- **Your name:** every approval from the HUD is then signed "Name (HUD)" in the receipt.
- **Shortcuts:** each key as key caps with a status (free, taken by another app, or can't be used). Click the caps and press a new combination. Chords Windows, Remote Desktop or AltGr use are refused with the reason.
- **Checks:** the same rows as `chaser doctor --online`.
- When no model can answer, the line saying so opens the Cloud key tab.
- On screen it's "Chaser" throughout, as the naming rule says. "Chaser Agent" stays the product name.

## Where things are kept

| What | Where |
|---|---|
| Settings (folder, port, packs, name, shortcuts, when onboarding finished) | `%LOCALAPPDATA%\ChaserAgent\settings.json`, or `CHASER_AGENT_HOME`. No secrets. |
| ChaseOS Cloud key | `%LOCALAPPDATA%\ChaserAgent\chaseos-cloud-key.dpapi`: Windows DPAPI for the current user, the same file `Save-ChaseOSCloudKey.ps1` writes, so the PowerShell scripts keep working. |
| Work, receipts, token | The private data folder, `%LOCALAPPDATA%\ChaserAgent\data` by default, readable only by you, SYSTEM and Administrators. |

A key in `CHASEOS_CLOUD_KEY` still comes first, so a vault that injects it (ChaseOS Studio's Secrets) keeps working. The service takes it out of its environment at start, as before.

## Limits

- The shortcuts are chosen and checked, but nothing holds them yet: they matter once Chaser controls the mouse and keyboard (mini-player HUD, phase 4).
- Saving a key needs Windows. Elsewhere, set `CHASEOS_CLOUD_KEY`.
- The key check needs ChaseOS Cloud to be reachable. If it isn't, the key is saved and the HUD says it couldn't be checked.

## Checks

- `tests/test_chaser_setup.py`: settings, the encrypted key round trip, the balance check against a local stand-in, shortcut rules, the checks, the HUD routes (token required, key never echoed, refused key not saved), and onboarding without a terminal.
- `scripts/check_hud.py`: the welcome card and all four steps in a hidden Edge window, with their own settings folder and a fake key.
