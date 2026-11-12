# Chaser Agent: setup and onboarding

12 November 2026. Chaser gets a first-run walk-through and one short command, `chaser`, in the terminal and in the HUD. It brings an easy panel to add and configure a Cloud key, a pre-flight check, a shortcuts panel, a simple command such as `chaser gateway`, and onboarding similar to OpenClaw's and Hermes'.

## Moat check

| Question | Answer |
|---|---|
| Could an agent rebuild it quickly? | Yes. A setup wizard, a key panel and a start command are a day's work for Claude Code or Codex. |
| Is there already a free or cheaper tool? | For their own agents, yes. OpenClaw has `openclaw onboard` (QuickStart or Advanced), `configure` and `doctor`. Hermes has `hermes setup`, `gateway` and `doctor --fix`. Neither sets up Chaser. |
| What stays hard to replace? | Nothing in the setup itself. It's table stakes: without it nobody but its developer can start Chaser. Its value is getting someone to their first receipted, approved task quickly. |
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
| `chaser model` | Choose how Chaser thinks: a menu of providers with ChaseOS Cloud first and recommended, then Claude (Claude Code sign-in), OpenRouter, OpenAI, Gemini, xAI, DeepSeek, Mistral, Groq, Together, Fireworks, Ollama and LM Studio on this computer, any other OpenAI-compatible endpoint, or another agent harness over the bridge. The key is pasted with no echo and saved encrypted for this Windows account; it's checked for free by listing the provider's models, which are then offered to choose from. `show`, `list`, and `set PROVIDER --model NAME` for scripts. |
| `chaser waiting` | What needs your answer or your yes, oldest first, each with the command that answers it. |
| `chaser sessions` | Recent work: title, where it stands, how long ago, its id. |
| `chaser approve [SESSION]`, `chaser reject [SESSION]` | Shows the exact request and its digest, then signs the decision "Name (terminal)". With one approval waiting, no id is needed. `chaser decide` still works. |
| `chaser receipt [SESSION]` | Reads the session's event log from disk and re-derives every hash, so it doesn't trust the running service: an edited line shows as "Chain broken at event N". Lists each approval with its signer and whether its digest matches the request, the tools run, and a SHA-256 of every file the session wrote. `--json` for scripts. `/receipt` in chat does the same. |
| `chaser channels` | Telegram and Discord (below): `add`, `test`, `remove`, `run` in the foreground. |
| `chaser stop` | The kill switch: cancels every session that is working or waiting. The service keeps running; nothing is deleted. `/stopall` does the same from a channel. |
| `chaser voice` | `status`, or `set FOLDER` to point at a pinned offline speech model; then `/voice` in chat. |
| `chaser status` | Running or not, every route's state, sessions, what's waiting, start at sign-in. Same as `chaser gateway status`. |
| `chaser logs [-f]` | The service log. Same as `chaser gateway logs`. |
| `chaser help [command]` | Every command, grouped; or one command's options. `?` on the home screen shows the same list. |
| `chaser version` | The installed version. |

`python -m chaser_agent …` runs the same command before the package is reinstalled with the new `chaser` entry point.

## The home menu

`chaser` on its own opens this, with ↑↓ and Enter or a letter, Esc to go back:

```
  Chaser Agent
  ● running on 127.0.0.1:8765   2 waiting for you   starts at sign-in
  Thinks with: ChaseOS Cloud, Claude Code
  Approvals signed "Sam"

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

Chaser is drawn beside the header in half-block pixels (two pixels a character, 24-bit colour), as Claude Code and Hermes show their marks. The pixels are scaled by `scripts/make_terminal_art.py` from the approved canon-core avatar export, with a feature-preserving rule so the face's constellation survives, and `chaser_art.py` records that file's path and hash; nothing is redrawn by hand, as the brand rule requires. The same art opens `chaser chat` and `chaser onboard`. It's left out without colour, in a window under 72 columns, or with `CHASER_NO_ART=1`.

The header is read from the running service each time the menu draws, so it shows the real state. **What's waiting** and **Recent work** list sessions and open the chosen one in chat. **Start at sign-in** asks before turning it on. Quitting the menu never stops Chaser.

## How Chaser thinks

Other harnesses lead their setup with their own service (Hermes recommends Nous Portal, a subscription signed in with OAuth). Chaser does the same with ChaseOS Cloud, and leaves the choice open: step 3 of onboarding and `chaser model` show ChaseOS Cloud first and recommended, then every other provider. Nothing is assumed: until a provider is chosen, the home screen shows the route Chaser picks automatically, marked "auto".

| Provider | How it connects |
|---|---|
| ChaseOS Cloud | Its own route, credits on the owner's key (`chaser key`) |
| Claude | The Claude Code sign-in on this computer; no key in Chaser |
| OpenRouter, OpenAI, Gemini, xAI, DeepSeek, Mistral, Groq, Together, Fireworks | One general route for OpenAI-style chat APIs, a key per provider |
| Ollama, LM Studio | The same route to a server on this computer; no key, nothing leaves the machine |
| Any other OpenAI-compatible endpoint | The same route to the address given (vLLM, LiteLLM, a company gateway) |
| Another agent harness | The bridge: Hermes or any harness answers over the local API |

Every provider keeps the existing rules: the chosen one comes first so "auto" uses it, a refusal or empty balance stops the turn and says so, and nothing switches provider behind the person's back. Keys live in `%LOCALAPPDATA%\ChaserAgent\keys\<provider>.dpapi` (the ChaseOS Cloud key stays in its existing file), and a key in the provider's usual variable (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`...) wins, so a vault still works. The key leaves the service's environment at start, so tools never inherit it. Base addresses were taken from the providers' own documentation; Nous Portal isn't listed because it signs in with OAuth rather than a key, so it's reached through Hermes on the bridge.

## Permission modes

Each session has a mode, recorded in its receipt with who set it:

| Mode | What runs without asking | How to choose it |
|---|---|---|
| `ask` (default) | Read-only and local tools that don't need approval; everything else waits for a named yes | nothing to do |
| `plan` | Only read-only tools; anything that changes or sends is refused, and Chaser is told to describe what it would do instead | `chaser chat --mode plan`, `/mode plan` |
| `bypass` | Every approval is said yes to automatically, signed "automatic (bypass mode)" in the receipt | `chaser chat --mode bypass` or `/mode bypass`, then typing `bypass` to confirm. It shows in red on the prompt. Channels can't set it, and it is never a saved default. |

Answering an approval with `a` ("yes, and don't ask again for this tool here") allows that one tool for the rest of that session only; each later use is still written to the receipt as "automatic (always allowed this session)". The mode is enforced in the service, not in the model's instructions, so a long conversation can't lose it.

## Images and voice

- **Images as context:** drag an image file into the terminal (Windows Terminal types its path, and Chaser attaches it), `/paste` the clipboard image (for example a screenshot from Win+Shift+S), `/image PATH`, or `chaser chat --image FILE`. PNG, JPEG, WebP and GIF, up to 3 MB each and four per message. Telegram photos and Discord, Slack and email image attachments come through the same way. Each image is saved in the session's `inputs` folder and noted in the receipt with its SHA-256. Routes that read images (ChaseOS Cloud and the OpenAI-compatible providers) get them as image parts; if the model refuses them, Chaser says to choose a vision model. Other routes are told an image is attached and that they can't see it.
- **Voice:** `/voice` records one six-second take, transcribes it with the offline model on this computer, and shows the text; Enter sends it, `n` discards it. Nothing is sent before you confirm. It needs `pip install chaser-agent[voice-input]` and a pinned model folder (`chaser voice set FOLDER`). Not yet tried with a live microphone in this build.

## Chat

```
  Chaser · chat   /help for commands · Ctrl+C stops the current task · /quit to leave

you › Check what's waiting on me today
  Reading the open loops first.
  › chaseos_open_loops
  Chaser needs your yes for this exact action: mail_create_draft
    { "to": "sam@example.org", ... }
    digest 3f9a1c0e…
  Say yes? [y/n, Enter to leave it]  signed Sam (terminal) › y
  you: yes  signed Sam (terminal)

  Two replies are due today. A draft to Sam is ready in your outbox, not sent.
  Finished
```

- Each step streams in from the same hash-chained event log the HUD reads, so the terminal shows what the tools did, not what the model says it did.
- Questions are answered inline, by number or in words. An approval shows the exact request and its digest; the decision is signed "Name (terminal)". Enter leaves either for later, in the HUD or another chat.
- Ctrl+C stops the current task and keeps the chat open. `/quit` leaves; Chaser keeps running.
- Slash commands: `/new`, `/sessions`, `/waiting`, `/open` (the HUD), `/status`, `/route`, `/stop`, `/checks`, `/help`, `/quit`.

## Running all the time

- **The supervisor** (`chaser gateway run`, which `start` and sign-in both use) starts the service and starts it again if it stops: after 2 s, then 5, 15, 30 and 60 s while it keeps failing, and back to 2 s once it has stayed up for two minutes. Each restart is noted in `service.log` with the exit code. Tested on Windows 11: a killed service answered again within 4 seconds.
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
| Model choice | provider config | `model` (Nous Portal recommended, 40+ providers) | `chaser model` (ChaseOS Cloud recommended, 14 choices plus any OpenAI-compatible endpoint), `/route` in chat |
| Dashboard | `dashboard` | web UI (community) | `chaser open`: the HUD |
| Messaging channels | Telegram, Discord, WhatsApp and more | 20+: Telegram, Discord, Slack, WhatsApp, Signal and more | Telegram and Discord as governed doors; Slack, email, WhatsApp, Signal, Teams, Matrix planned |
| Schedules | cron | `cron` | none (see below) |
| Named approvals bound to the exact request | no | no | yes: digest-checked, signed by name in HUD and terminal |
| Hash-chained receipt for every step | no | no | yes |
| Outcome ledger and route scorecard | no | no | yes, in ChaseOS |

Chaser now matches both on setup, model choice, health, the background service, logs and terminal chat. Messaging channels start with Telegram and Discord, as governed doors (below); schedules come only through ChaseOS's existing ingestion owner rather than a second scheduler.

## Messaging channels

**Built: Telegram, Discord, Slack and email.** `chaser channels add telegram` takes the BotFather token (no echo), checks it, then asks you to message the bot from your own account and allowlists exactly that account. `chaser channels add discord` takes the bot token and your Discord user ID and says hello in a direct message. Tokens are saved encrypted for this Windows account (`keys\channel-<platform>.dpapi`, or `TELEGRAM_BOT_TOKEN` / `DISCORD_BOT_TOKEN` from a vault). The gateway's supervisor serves the channels beside the service, so they run whenever Chaser does.

- Only allowlisted accounts are heard; anyone else is ignored and noted in the service log.
- A message starts or continues that chat's session through the same local API as the terminal; `/new`, `/waiting` and `/stop` work there too.
- Steps arrive briefly ("Working: mail_search, read_document"), then the answer.
- An approval arrives with the tool, its arguments and the digest's first characters. Telegram shows Yes and No buttons carrying the approval id and digest prefix; Discord takes a typed yes or no. Before deciding, Chaser checks the answer refers to the request that is waiting now, then signs it "Name (Telegram)" or "Name (Discord)" into the receipt.
- None needs a public address: Telegram is long-polled; Discord and Slack are read from the bot's direct message with each allowed person over their web APIs; email is read over IMAP and answered over SMTP, both over TLS.
- **Slack:** `chaser channels add slack` takes the bot token (scopes `chat:write`, `im:history`, `im:write`, `files:read`) and your member ID.
- **Email:** `chaser channels add email` takes Chaser's address, the IMAP and SMTP servers (filled in for Gmail, Outlook and iCloud), an app password and the senders allowed to instruct it. A message counts only when the receiving server recorded a DKIM or SPF pass for the sender's own domain, because a From line can be forged; anything else is ignored and noted in the log. Mail threads can cross, so an approval by email must quote the start of the digest: "yes 9ac1f0e4".
- Photos and image attachments arrive as context (see Images and voice).

### The rest of the plan

Hermes reaches people on Telegram, Discord, Slack, WhatsApp, Signal, SMS, email, Matrix, Mattermost, Teams, LINE and more; OpenClaw has a similar list. Chaser will have them, built as governed doors rather than plain chat bridges.

**Moat check.** An agent could build a Discord or Telegram adapter in an afternoon, and Hermes and OpenClaw already do it for free, so the adapters themselves are no moat. What stays hard to copy is what happens at the door: a message starts a session that still stops at every approval; the approval reaches the person in the same app with the exact request and its digest; only allowlisted people can answer; the decision is signed by name ("Sam (Discord)") into the session's hash-chained receipt; and anything the reply would send out counts as leaving the computer, so it needs that same yes. Neither harness binds a channel approval to the request digest or writes it into a receipt.

**Order, by reach and effort:**

1. Discord, Telegram, Slack and email: built (above).
2. WhatsApp (official Cloud API), Signal (through signal-cli), Microsoft Teams, Matrix.
3. Others on request: Mattermost, Google Chat, SMS, LINE, ntfy for notifications only.

**Shape.** Each new platform is one adapter class with `poll`, `send` and `acknowledge`; the door (allowlist, approvals bound to the digest, signing) is shared and already tested. Schedules still go only through ChaseOS's existing ingestion owner.

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
