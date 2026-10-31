# Chaser Agent HUD

The way to see and steer the running agent. It's a small window that stays above your other work, not a dashboard. `chaser-agent open` starts it. Closing or minimizing it doesn't stop the agent, and Stop is the only control that does.

## What it shows

**The pill**, 420 by 76 pixels in the bottom-right corner:

- the character, playing the approved motion for the real state
- one word for the state, in a colour: blue working, amber needs you, teal finished, red stopped
- how long it has run, how many steps it has taken, and how many were refused or failed
- one line saying what it's doing right now
- Stop, whenever there's something to stop

**The panel** opens upward from the pill when you click it:

- the goal, and which step of the plan it's on
- a list with one row per action, tagged `READ`, `SAVED`, `DRAFT`, `REFUSED` or `FAILED`
- a question or approval, pinned above the input until it's answered
- one input to tell it what to do
- Earlier work, Files, and a link out to the parent application if a pack sets one

Open any row to see why it did that, exactly what it asked for and what came back. That's the whole point of the HUD: you can check what the agent did without reading a log.

The panel opens by itself only when the agent needs you or has stopped. Esc closes it. A window that's minimized keeps following the work and shows a waiting question in its taskbar title.

A file opens in the same window, which grows while you read it. It's shown in a sandboxed frame, because a generated page isn't trusted.

## What it leaves out

The earlier console had three columns: routes, sessions, a timeline, a plan, files and the tools allowed. That's a control room, and the parent application is the place for a control room. When no model can answer, the HUD says so in one line and the reasons are in that line's tooltip. Tool grants remain in the session record and the event log.

## What other agent interfaces do

These are the practices it follows, and the source for each. Quality varies: most of these are community reports, third-party add-ons and product pages, not design studies. Nothing specific was found on how Manus, ChatGPT agent or Grok Bot lay out their progress views, so they aren't claimed here.

| Practice | Where it was seen | In this HUD |
|---|---|---|
| A small status pill you can read at a glance | [AgentsRoom Live Activities](https://agentsroom.dev/de/features/live-activities) | The pill |
| One current step out of a visible list | [Codex progress panel, user report](https://community.openai.com/t/how-do-i-show-the-live-codex-task-progress-view-in-the-unified-chatgpt-desktop-app/1387429) | Now line and `Step 3 of 10` |
| Short action tags such as READ, EDIT, EXEC | [hud](https://www.everydev.ai/tools/hud-mode/llms.txt), [claude-hud-enhanced](https://skillselion.com/plugin/alwinpaul1/claude-hud-enhanced) | Row tags, taken from each tool's declared side effect |
| See what's running and click to inspect | [Claude Code status-line request](https://claudeissues.com/issue/40928-feature-request-show-running-agents-in-status-line-with-click-to-focus) | Rows open in place |
| Stop is a separate control from approve, and always reachable | [Override versus approval](https://iamstackwell-com.pages.dev/posts/ai-agent-human-override/), [replacing pause with takeover](https://gsdms.csir.co.za/aanews1/enhancing-gui-agents-replacing-pause) | Stop in the pill. Approvals pinned in the panel |
| Ask only for what can't be undone | [Approval by reversibility](https://vp0.com/blogs/human-in-the-loop-approval-swipe-ui) | Reads never ask. Approvals are bound to the exact request |
| An activity feed that doubles as an audit trail | [Agent UX skill](https://claudskills.com/skills/ai-agent-ux/SKILL.md) | Rows come from the hash-chained event log, never from the model's own account |
| Show concrete examples before asking someone to navigate | "Increment: Scented Navigation", a retained paper on incremental knowledge graph queries | Up to three real examples when nothing is running |

## Where it differs from those

Most of them report what an agent says it's doing. This one shows what the tools actually did, because the rows come from the event log. A refusal or failure appears as its own row in red, because the point of the agent is that a blocked route never passes for progress.

## Windows

`chaser-agent open` starts Edge as an app window, keeps it above other windows and places it above the taskbar. The page resizes its own window from the bottom-right, so the pill doesn't move when the panel opens. In an ordinary browser tab it can't resize itself, and the same layout still works.

The older Tk overlay in [Chaser-Agent-Computer-Use-HUD.md](Chaser-Agent-Computer-Use-HUD.md) is for computer-use sessions that receive their state from a harness. It's a separate surface.
