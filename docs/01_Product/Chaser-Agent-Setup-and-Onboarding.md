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
| `chaser` | The home menu (below). Offers onboarding if it hasn't run. Without a console it prints the status and the commands instead. |
| `chaser chat` (or `tui`) | Talk to Chaser and watch it work (below). `--session` carries on earlier work, `--route` picks how new work thinks. |
| `chaser onboard` | First run, in six steps: check this computer, create the private data folder (or use this computer's existing ChaseOS setup for Chaser, if it has one), add a ChaseOS Cloud key (optional), your name on approvals, the stop shortcuts, start Chaser and open the HUD. **QuickStart** asks only for the key and the name; **Advanced** also asks for the folder, port and packs. `--non-interactive` takes flags and asks nothing; `--use-chaseos` takes the existing ChaseOS setup; `--reset` starts from default settings but keeps work, receipts and the key. |
| `chaser gateway` | Starts Chaser in the background under a supervisor, out of the terminal's process group, and waits until it answers. `stop`, `restart`, `status` (routes, sessions, start at sign-in), `logs` (`-f` to follow), `run` (the supervisor in this terminal), `install` and `uninstall` (start at sign-in). `stop` also stops a service started by `Start-ChaserAgent.ps1`. |
| `chaser setup` | The same arrow-key menu for every setting: key, folder and port, name, packs, shortcuts, checks, start or stop. `chaser setup key` jumps to one section. |
| `chaser doctor` | Pre-flight checks. `--online` also asks ChaseOS Cloud for the key's balance, which costs nothing; `--fix` creates the private data folder; `--json` for scripts. |
| `chaser key` | `status`, `add` (pasted with no echo), `check` and `remove`. If Chaser is running, it uses a new key at once. |
| `chaser shortcuts` | Shows the stop and take-over keys and whether each is free. `set stop Ctrl+Alt+Shift+X`, or `reset`. |
| `chaser ask`, `open`, `decide`, `agent-status` | The existing commands, using the folder and port from settings, so they need no flags. |

`python -m chaser_agent …` runs the same command before the package is reinstalled with the new `chaser` entry point.

## The home menu

`chaser` on its own opens this, with ↑↓ and Enter or a letter, Esc to go back:

```
  Chaser Agent
  ● running on 127.0.0.1:8765   2 waiting for you   starts at sign-in
  Thinks with: ChaseOS Cloud, Claude Code
  Approvals signed "Chase"

  › c  Chat with Chaser
    w  What's waiting for you    2
    r  Recent work
    h  Open the HUD
    g  Stop Chaser
    a  Start at sign-in          on
    s  Settings                  key, folder, name, packs, shortcuts
    d  Checks
    l  Logs                      live
    q  Quit                      Chaser keeps running
```

The header is read from the running service each time the menu draws, so it shows the real state. **What's waiting** and **Recent work** list sessions and open the chosen one in chat. **Start at sign-in** asks before turning it on. Quitting the menu never stops Chaser.

## Chat

```
  Chaser · chat   /help for commands · Ctrl+C stops the current task · /quit to leave

you › Check what's waiting on me today
  Reading the open loops first.
  › chaseos_open_loops
  Chaser needs your yes for this exact action: mail_create_draft
    { "to": "sam@example.org", ... }
    digest 3f9a1c0e…
  Say yes? [y/n, Enter to leave it]  signed Chase (terminal) › y
  you: yes  signed Chase (terminal)

  Two replies are due today. A draft to Sam is ready in your outbox, not sent.
  Finished
```

- Each step streams in from the same hash-chained event log the HUD reads, so the terminal shows what the tools did, not what the model says it did.
- Questions are answered inline, by number or in words. An approval shows the exact request and its digest; the decision is signed "Name (terminal)". Enter leaves either for later, in the HUD or another chat.
- Ctrl+C stops the current task and keeps the chat open. `/quit` leaves; Chaser keeps running.
- Slash commands: `/new`, `/sessions`, `/waiting`, `/open` (the HUD), `/status`, `/route`, `/stop`, `/checks`, `/help`, `/quit`.

## Running all the time

- **The supervisor** (`chaser gateway run`, which `start` and sign-in both use) starts the service and starts it again if it stops: after 2 s, then 5, 15, 30 and 60 s while it keeps failing, and back to 2 s once it has stayed up for two minutes. Each restart is noted in `service.log` with the exit code. Tested on ORITECHNE: a killed service answered again within 4 seconds.
- **Stopping is a request, not a race:** `chaser gateway stop` leaves a stop file the supervisor reads, so it stops the service and exits rather than restarting it.
- **Start at sign-in** (`chaser gateway install`) adds a per-user entry under Windows' `Run` key that starts the supervisor with `pythonw`, so no console window opens. No admin rights, no Windows service, no scheduled task. `uninstall` removes the entry.
- **Out of the terminal's process group:** the background supervisor is started detached and outside the launching terminal's job, so closing the terminal doesn't end Chaser.
- **Nothing scheduled:** the supervisor keeps the service answering. It runs no jobs of its own; Chaser still works only on what the HUD, the terminal or a pack asks.

## Against OpenClaw and Hermes

Read on 12 November 2026 from their CLI references (OpenClaw: docs.openclaw.ai/cli; Hermes: hermes-agent.nousresearch.com/docs/reference).

| Capability | OpenClaw | Hermes | Chaser now |
|---|---|---|---|
| Guided first run | `onboard` (QuickStart, Advanced, non-interactive) | `setup` (whole or per section) | `chaser onboard`, same three paths, plus ChaseOS detection |
| Change settings later | `configure` | `setup <section>`, `model`, `tools` | `chaser setup`, `chaser key`, `chaser shortcuts`, HUD Settings |
| Health check | `doctor`, `health` | `doctor [--fix]` | `chaser doctor [--online] [--fix]`, sign-in tested by the running service |
| Background service | `gateway install/start/stop/restart/run` | `gateway install/start/stop/status` | `chaser gateway` with a supervisor, `install`/`uninstall` at sign-in |
| Logs | `logs --follow` | `logs` | `chaser gateway logs -f` |
| Terminal chat | `tui`, `chat` | the CLI, `--tui` | `chaser chat` with streamed steps, inline approvals, slash commands |
| Model choice | provider config | `model`, `/model` | `/route` in chat; the route scorecard recommends one |
| Dashboard | `dashboard` | web UI (community) | `chaser open`: the HUD |
| Messaging channels | Telegram, Discord, WhatsApp and more | Telegram, Discord and more | none (see below) |
| Schedules | cron | `cron` | none (see below) |
| Named approvals bound to the exact request | no | no | yes: digest-checked, signed by name in HUD and terminal |
| Hash-chained receipt for every step | no | no | yes |
| Outcome ledger and route scorecard | no | no | yes, in ChaseOS |

Chaser now matches both on setup, health, the background service, logs and terminal chat. It deliberately has no messaging channels or schedules yet: each is a way for work to start or results to leave without the person at the computer, which is exactly what Chaser governs. They come only behind the same approvals and receipts, and schedules only through ChaseOS's existing ingestion owner rather than a second scheduler.

## Tuning toward the moat

The setup and terminal are table stakes; both harnesses have them and an agent can rebuild them. What stays hard to replace is what every screen now leads to: **who approved what, the receipt behind it, and whether the answer was any good.** The next changes put those at the front, in order of how much they move the 31 January kill test:

1. **A verdict after every finished task, in chat and the HUD:** Accept, Edited or Reject, written into the session's event chain and read by the outcome ledger. Today verdicts are only given in Personal Command. Asking at the moment the answer lands is what fills the scorecard (verdict coverage is the kill-test number most behind).
2. **`/receipt` in chat and "Verify" in the HUD:** run `verify_chain` on the session and show the chain head, each approval with its signer and digest, and the output hashes. That makes the receipt something a customer can be shown, not just a file.
3. **The route scorecard in `chaser` and `/route`:** show each route's acceptance and cost per accepted answer beside the route names, and default `/route` to the scorecard's pick once a workflow has 20 verdicts.
4. **Time to answer on the home menu:** "2 waiting for you, oldest 14 minutes" from `approval_requested` → now. It's the HUD's own kill-test number, shown where the person already looks.
5. **Channels and schedules only as governed doors:** if they come, a message or a schedule starts a session that still stops at every approval, with the request and its digest sent to the person and the decision signed. Without that they'd make Chaser one more generic harness.

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
