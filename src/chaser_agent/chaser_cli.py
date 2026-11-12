"""`chaser`: set up, start, talk to and check Chaser Agent from a terminal.

    chaser                 the home menu: chat, what's waiting, the HUD, start or stop, settings, checks, logs
    chaser chat            talk to Chaser and watch it work; answer questions and approvals inline
    chaser onboard         first-run setup: checks, folder, key, your name, shortcuts, start
    chaser gateway         start Chaser in the background, kept running by a supervisor
                           (stop, restart, status, logs [-f], run, install, uninstall)
    chaser setup           change any setting from a menu
    chaser doctor          pre-flight checks (--online also checks the key, --fix creates the folder)
    chaser model           choose the AI provider and model (ChaseOS Cloud recommended; any works)
    chaser key             add, check or remove the ChaseOS Cloud key (never shown)
    chaser shortcuts       the keys that stop Chaser or take over
    chaser open            the HUD
    chaser ask "..."       give Chaser a task and follow it
    chaser help            every command

Everything else `chaser-agent` does still works, and `chaser ask`, `open`, `decide` and `agent-status`
use the folder and port from your settings, so you never pass them.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from chaser_agent import (channels, chaser_home, chaser_work, cloud_key, gateway_service, model_providers as providers, setup_checks, shortcuts, terminal_art, terminal_theme,
                          terminal_ui)

PASS_THROUGH = {"ask", "open", "decide", "agent-status", "reasoner"}
# The one line under the greeting on the home screen.
INTRO = ("Your agent on this computer.", "Every step gets a receipt; nothing leaves without your yes.")
MARK = {"ok": "✓", "warn": "!", "fail": "✗", "info": "·"}
_colour = False
_full = True  # 24-bit colour; False falls back to the 256-colour palette


# --- Output -------------------------------------------------------------------

def _setup_terminal() -> None:
    global _colour, _full
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _colour = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    _full = terminal_theme.truecolor()
    if _colour and os.name == "nt":
        os.system("")  # turns on colour codes in the Windows console


def interactive_terminal() -> bool:
    """A person at a console. On Windows, input from NUL also claims to be a terminal, so ask the console itself."""
    if not sys.stdin.isatty():
        return False
    if os.name != "nt":
        return True
    import ctypes
    import msvcrt

    mode = ctypes.c_ulong()
    try:
        return bool(ctypes.windll.kernel32.GetConsoleMode(msvcrt.get_osfhandle(sys.stdin.fileno()), ctypes.byref(mode)))
    except OSError:
        return False


def paint(text: str, tone: str) -> str:
    return terminal_theme.paint(text, tone, colour=_colour, full=_full)


def heading(text: str) -> None:
    print("\n  " + paint("▍", "teal") + paint(text, "head"))


def step(number: int, total: int, text: str) -> None:
    """An onboarding step: progress dots, then the step's name."""
    dots = paint("●" * number, "teal") + paint("○" * (total - number), "line")
    print(f"\n  {dots}  {paint(text, 'head')}  {paint(f'{number} of {total}', 'dim')}")


def show_rows(rows: list[dict[str, Any]]) -> None:
    width = max(len(item["title"]) for item in rows)
    for item in rows:
        print(f"  {paint(MARK[item['state']], item['state'])} {item['title']:<{width}}  {item['detail']}")
        if item.get("fix") and item["state"] in {"warn", "fail"}:
            print(f"    {' ' * width}  {paint('→ ' + item['fix'], 'dim')}")


def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        value = input(f"  {prompt}{hint}: ").strip()
    except EOFError:
        value = ""
    return value or default


def confirm(prompt: str, default: bool = True) -> bool:
    answer = ask(f"{prompt} {'[Y/n]' if default else '[y/N]'}").lower()
    return default if not answer else answer.startswith("y")


# --- The service ----------------------------------------------------------------

def gateway_command(settings: dict[str, Any]) -> list[str]:
    return gateway_service.service_command(settings)


def gateway_start(settings: dict[str, Any], *, wait: float = 60) -> tuple[bool, str]:
    return gateway_service.start_detached(settings, wait=wait)


def gateway_stop(settings: dict[str, Any]) -> tuple[bool, str]:
    return gateway_service.stop(settings)


# --- Talking to the running service ------------------------------------------

def _service_call(settings: dict[str, Any], method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
    from chaser_agent import agent_cli

    args = argparse.Namespace(data_dir=str(settings["data_dir"]), port=int(settings["port"]))
    return agent_cli._call(args, method, path, body)


def _routes(settings: dict[str, Any]) -> list[dict[str, Any]] | None:
    """The running service's own route checks, which test sign-in. None when Chaser isn't running."""
    if not _running(settings):
        return None
    status, reply = _service_call(settings, "GET", "/v1/agent/status")
    if status == 200 and not (reply.get("reasoners") or {}).get("routes"):
        time.sleep(2)  # routes are checked in the background the first time anyone asks
        status, reply = _service_call(settings, "GET", "/v1/agent/status")
    return ((reply.get("reasoners") or {}).get("routes") or None) if status == 200 else None


def _running(settings: dict[str, Any]) -> bool:
    health = setup_checks.gateway_health(int(settings["port"]))
    return bool(health and health.get("service") == "chaser-agent" and health.get("agent") == "ready")


# --- Pieces shared by onboarding and the menu ----------------------------------

def step_key(settings: dict[str, Any], *, offer: bool = True) -> None:
    found = cloud_key.describe()
    if found["source"] == "environment":
        print(f"  {paint('✓', 'ok')} Your vault gives Chaser a ChaseOS Cloud key for this session.")
        return
    if found["source"] == "saved":
        print(f"  {paint('✓', 'ok')} A ChaseOS Cloud key is saved for this Windows account.")
        if not confirm("Replace it?", default=False):
            return
    elif offer and not confirm("Add a ChaseOS Cloud key now?"):
        print(f"  {paint('·', 'info')} Skipped. Add one any time: chaser key add")
        return
    add_key(settings)


class SecretInputUnavailable(RuntimeError):
    """This terminal can't take a secret without showing it, so none is read."""


def secret_input(prompt: str) -> str:
    """Read a secret with one dot per character on screen, so a paste visibly lands, and never the characters.

    Python's getpass quietly falls back to echoing (with only a warning) when it decides stdin isn't the console;
    Chase saw his key printed while pasting it on 12 Nov 2026. This reads the console directly on Windows and
    refuses rather than echo when there is no console to read.
    """
    if not sys.stdin or not sys.stdin.isatty():
        raise SecretInputUnavailable("This window can't hide what you type, so the key wasn't read. Open PowerShell or Windows Terminal and run: chaser key add")
    if os.name != "nt":
        return getpass.getpass(prompt)
    import msvcrt
    sys.stdout.write(prompt)
    sys.stdout.flush()
    chars: list[str] = []
    while True:
        ch = msvcrt.getwch()
        if ch in ("\r", "\n"):
            break
        if ch == "\x03":                      # Ctrl+C
            sys.stdout.write("\n")
            raise KeyboardInterrupt
        if ch in ("\x00", "\xe0"):            # arrow and function keys arrive as two characters: ignore both
            msvcrt.getwch()
            continue
        if ch in ("\b", "\x7f"):
            if chars:
                chars.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue
        if ch == "\x15":                      # Ctrl+U clears the line
            sys.stdout.write("\b \b" * len(chars))
            chars.clear()
            sys.stdout.flush()
            continue
        if ch < " ":
            continue
        chars.append(ch)
        sys.stdout.write("•")
        sys.stdout.flush()
    sys.stdout.write(f"  ({len(chars)} characters)\n" if chars else "\n")
    sys.stdout.flush()
    return "".join(chars)


def _say_check(result: dict[str, Any], *, saved: bool) -> None:
    """Always say plainly whether ChaseOS Cloud accepted the key."""
    if result.get("ok"):
        credits = f", {result['credits']:,.0f} credits left" if result.get("credits") is not None else ""
        print(f"  {paint('✓', 'ok')} Valid: ChaseOS Cloud accepts this key{credits}.")
    elif result.get("refused"):
        print(f"  {paint('✗', 'fail')} Not valid: {result.get('reason')}" + (" It was saved anyway; add the right one with: chaser key add" if saved else ""))
    else:
        print(f"  {paint('!', 'warn')} Not confirmed yet: {result.get('reason') or 'ChaseOS Cloud did not say.'} Check again with: chaser key check")


def link(url: str, text: str | None = None) -> str:
    """A clickable terminal link (OSC 8: Windows Terminal, VS Code and most modern terminals) that still reads as the
    plain address where links aren't supported."""
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return url
    return f"\x1b]8;;{url}\x1b\\{text or url}\x1b]8;;\x1b\\"


def add_key(settings: dict[str, Any]) -> bool:
    from chaser_agent.model_providers import KEYS_PAGE
    print(f"  Get a key at {link(KEYS_PAGE)}  (Ctrl+click to open; sign in or create an account, then make a Cloud key)")
    print(paint("  Each character shows as a dot, never the key itself.", "dim"))
    try:
        key = secret_input("  ChaseOS Cloud key: ")
    except SecretInputUnavailable as exc:
        print(f"  {paint('✗', 'fail')} {exc}")
        return False
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    try:
        key = cloud_key.validate(key)
    except ValueError as exc:
        print(f"  {paint('✗', 'fail')} {exc}")
        return False
    if _running(settings):
        status, reply = _service_call(settings, "POST", "/v1/agent/setup/key", {"key": key})
        if status == 404:
            print(paint("  The Chaser Agent running now is an older build that can't take a key while it runs (your key is fine).\n"
                        "  The key is saved here and used when Chaser Agent next starts: chaser gateway restart", "dim"))
            return _save_key_here(key)
        if status == 200:
            check = reply.get("check") or cloud_key.check(key)
            print(f"  {paint('✓', 'ok')} Saved for this Windows account only, and Chaser is using it now.")
            _say_check(check, saved=True)
            return not check.get("refused")
        message = (reply.get("error") or {}).get("message") if isinstance(reply, dict) else None
        print(f"  {paint('✗', 'fail')} {message or 'Chaser could not save the key.'}")
        return False
    return _save_key_here(key)


def _save_key_here(key: str) -> bool:
    print("  Checking it with ChaseOS Cloud…")
    result = cloud_key.check(key)
    if result.get("refused"):
        _say_check(result, saved=False)
        print("  Nothing was saved.")
        return False
    try:
        cloud_key.save(key)
    except cloud_key.KeyStoreUnavailable as exc:
        print(f"  {paint('✗', 'fail')} {exc}")
        return False
    print(f"  {paint('✓', 'ok')} Saved for this Windows account only.")
    _say_check(result, saved=True)
    return True


def _pick_model(ids: list[str], default: str) -> str:
    """Type a model's name or part of it; several matches are listed to narrow down."""
    if ids:
        print(paint(f"  {len(ids)} models available. Type part of a name to search, or Enter for the default.", "dim"))
    while True:
        typed = ask("Model", default)
        if not typed:
            print(f"  {paint('!', 'warn')} Choose a model.")
            continue
        if not ids or typed in ids:
            return typed
        matches = [i for i in ids if typed.lower() in i.lower()]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            if confirm(f"{typed} isn't in the provider's list. Use it anyway?", default=False):
                return typed
            continue
        for item in matches[:15]:
            print("    " + paint(item, "teal"))
        if len(matches) > 15:
            print(paint(f"    … and {len(matches) - 15} more; type more of the name", "dim"))
        default = ""


def cloud_key_step(settings: dict[str, Any]) -> bool:
    """ChaseOS Cloud: 'I already have a key' pastes it; 'Get a key' opens the account page first. True once a key is in."""
    if cloud_key.describe()["source"] != "none":
        step_key(settings, offer=False)
        return True
    items = [terminal_ui.Item("1", "I already have a key", "paste it; it won't show"),
             terminal_ui.Item("2", "Get a key", "opens chaseos.ai to sign in or create an account and make one")]
    picked = terminal_ui.select("", items, header=[paint("ChaseOS Cloud", "head"), paint("One key, credits on your account, built for Chaser.", "dim")],
                                paint=paint, interactive=interactive_terminal())
    print("\033[2J\033[H", end="")
    if picked is None:
        return False
    if picked == "2":
        import webbrowser

        opened = webbrowser.open(providers.KEYS_PAGE)
        print(f"  {paint('→', 'teal')} " + ("Opened " if opened else "Open ") + paint(providers.KEYS_PAGE, "teal")
              + (" in your browser." if opened else " in your browser."))
        print(paint("  Sign in or create an account, make a Cloud key and copy it. Then come back here.", "dim"))
        if not confirm("Got it copied? Paste it now", default=True):
            print(f"  {paint('·', 'info')} Add it any time: chaser key add")
            return False
    return bool(add_key(settings))


def choose_model(settings: dict[str, Any], *, interactive: bool = True, only: list[Any] | None = None,
                 title: str = "Choose how Chaser thinks",
                 subtitle: str = "ChaseOS Cloud is built for Chaser, but any provider works and you can change it any time.") -> dict[str, Any]:
    """Pick the provider and model Chaser thinks with. ChaseOS Cloud is first and recommended; any of them works.

    Claude Code sign-in and other harnesses sit under Advanced: subscriptions can stop working without
    warning and their terms usually aren't meant to power another agent."""
    current = settings.get("provider") or providers.DEFAULT
    shown = only or sorted(providers.CATALOGUE, key=lambda p: providers.GROUPS.index(providers.group(p)))
    items = []
    for index, provider in enumerate(shown):
        key = "123456789abcdefghijklmnop"[index]
        hint = ("● current · " if provider.id == settings.get("provider") else "") + provider.blurb
        items.append(terminal_ui.Item(key, provider.label, hint, providers.group(provider)))
    intro = [paint(title, "head"), paint(subtitle, "dim")]
    picked = terminal_ui.select("", items, header=intro, paint=paint, interactive=interactive and interactive_terminal(),
                                start=next((i.key for i, p in zip(items, shown) if p.id == current), None))
    print("\033[2J\033[H", end="")
    if picked is None:
        return settings
    provider = shown[[i.key for i in items].index(picked)]
    print(paint(f"  {provider.label}", "head") + paint(f"  {provider.blurb}", "dim"))
    if provider.kind == "chaseos":
        cloud_key_step(settings)
        settings = chaser_home.save({"provider": provider.id, "model": "", "base_url": ""})
    elif provider.kind == "claude-cli":
        found = shutil.which("claude")
        print(f"  {paint('✓', 'ok')} Claude Code is installed." if found else
              f"  {paint('!', 'warn')} Claude Code isn't installed here. Install it and sign in, then Chaser can use it.")
        settings = chaser_home.save({"provider": provider.id, "model": "", "base_url": ""})
    elif provider.kind == "bridge":
        print(paint("  Another harness answers Chaser's requests over its local API:\n"
                    "    chaser reasoner next   then   chaser reasoner reply ID --file reply.json", "dim"))
        settings = chaser_home.save({"provider": provider.id, "model": "", "base_url": ""})
    else:
        base_url = provider.base_url
        if provider.id == "custom":
            base_url = ask("The endpoint's address, up to /v1", settings.get("base_url") or "").rstrip("/")
            if not base_url:
                return settings
        key = ""
        if provider.needs_key:
            existing, source = providers.load_key(provider.id)
            if source == "environment":
                print(f"  {paint('✓', 'ok')} Using the key in {provider.key_env} from your environment.")
                key = existing
            elif existing and not confirm(f"A {provider.label} key is saved. Replace it?", default=False):
                key = existing
            else:
                if provider.keys_page:
                    print(paint(f"  Get a key at {provider.keys_page}. It won't show as you paste it.", "dim"))
                try:
                    key = cloud_key.validate(secret_input(f"  {provider.label} key: "))
                except (ValueError, SecretInputUnavailable) as exc:
                    print(f"  {paint('✗', 'fail')} {exc}")
                    return settings
                except (EOFError, KeyboardInterrupt):
                    print()
                    return settings
        print(f"  Checking with {provider.label}…")
        status, ids = providers.list_models(base_url, key)
        if status in {401, 403}:
            print(f"  {paint('✗', 'fail')} {provider.label} refused that key (HTTP {status}). Nothing was saved.")
            return settings
        if status == 200:
            print(f"  {paint('✓', 'ok')} Connected.")
        else:
            print(f"  {paint('!', 'warn')} Couldn't list its models ({'no connection' if not status else 'HTTP ' + str(status)}). You can still type one.")
        model = _pick_model(ids, settings.get("model") if settings.get("provider") == provider.id else provider.model)
        if key and providers.load_key(provider.id)[1] != "environment":
            try:
                providers.save_key(provider.id, key)
            except cloud_key.KeyStoreUnavailable as exc:
                print(f"  {paint('✗', 'fail')} {exc}")
                return settings
        settings = chaser_home.save({"provider": provider.id, "model": model,
                                     "base_url": base_url if provider.id == "custom" else ""})
    print(f"  {paint('✓', 'ok')} Chaser thinks with {providers.describe(settings)}.")
    if _running(settings) and confirm("Restart Chaser so it uses this now?"):
        print("  " + gateway_stop(settings)[1])
        print("  " + gateway_start(settings)[1])
    return settings


def step_power(settings: dict[str, Any]) -> dict[str, Any]:
    """Onboarding's question: what will power Chaser? ChaseOS Cloud (recommended) or your own key."""
    items = [terminal_ui.Item("1", "ChaseOS Cloud", "recommended · one key, credits, built for Chaser"),
             terminal_ui.Item("2", "Bring your own key (BYOK)", "OpenRouter, OpenAI, Gemini, DeepSeek… or a model on this computer")]
    header = [paint("What will power Chaser?", "head"),
              paint("You can change this any time with chaser model, which also has Claude Code sign-in and other harnesses.", "dim")]
    picked = terminal_ui.select("", items, header=header, paint=paint, interactive=interactive_terminal())
    print("\033[2J\033[H", end="")
    if picked is None:
        print(f"  {paint('·', 'info')} Skipped. Choose any time: chaser model")
        return settings
    if picked == "1":
        cloud_key_step(settings)
        settings = chaser_home.save({"provider": providers.DEFAULT, "model": "", "base_url": ""})
        print(f"  {paint('✓', 'ok')} Chaser thinks with ChaseOS Cloud.")
        return settings
    return choose_model(settings, only=providers.byok(), title="Bring your own key",
                        subtitle="A key from any of these, or a model on this computer. Keys are saved encrypted for this Windows account.")


def step_name(settings: dict[str, Any]) -> dict[str, Any]:
    print(paint("  Every yes or no you give Chaser is signed with this name, so its receipts show who decided.", "dim"))
    name = " ".join(ask("Your name", settings.get("reviewer") or "").split())[:60]
    if name:
        settings = chaser_home.save({"reviewer": name})
        print(f"  {paint('✓', 'ok')} Approvals will be signed \"{name}\".")
    return settings


def show_shortcuts(settings: dict[str, Any]) -> None:
    words = {"free": paint("free", "ok"), "taken": paint("taken by another app", "warn"), "unknown": paint("not checked here", "dim"), "invalid": paint("can't be used", "fail")}
    for item in shortcuts.overview(settings["shortcuts"]):
        keys = " + ".join(item["keys"]) if item["keys"] else item["chord"]
        print(f"  {item['title']:<36} {keys:<24} {words[item['state']]}")
    print(paint("  Take over also happens the moment you move the mouse or type. Only you can resume.", "dim"))
    print(paint("  Chaser holds these keys once it can use the mouse and keyboard. Change them: chaser shortcuts set", "dim"))


def _offer_chaseos(found: dict[str, Any]) -> bool:
    print(f"  This computer already has a ChaseOS setup for Chaser ({found['source']}):")
    print(paint(f"    folder {found['data_dir']}\n    port {found['port']}, {len(found['packs'])} pack(s)", "dim"))
    return confirm("Use it, so Chaser keeps its existing work and receipts?")


def step_start(settings: dict[str, Any], *, open_hud: bool = True) -> bool:
    print("  Starting Chaser…")
    ok, message = gateway_start(settings)
    print(f"  {paint('✓' if ok else '✗', 'ok' if ok else 'fail')} {message}")
    if ok and open_hud:
        from chaser_agent import agent_cli

        agent_cli.run_open(argparse.Namespace(data_dir=str(settings["data_dir"]), port=int(settings["port"])))
    return ok


# --- Commands -------------------------------------------------------------------

def run_onboard(args: argparse.Namespace) -> int:
    if args.reset:
        chaser_home.settings_path().unlink(missing_ok=True)
        print("Your settings were reset. Your work, receipts and saved key are kept.")
    settings = chaser_home.load()
    changes: dict[str, Any] = {}
    for name in ("data_dir", "port", "reviewer"):
        if getattr(args, name) not in (None, ""):
            changes[name] = getattr(args, name)
    if args.pack:
        changes["packs"] = [str(Path(p).resolve()) for p in args.pack]
    if changes:
        settings = chaser_home.save(changes)
    interactive = not args.non_interactive and interactive_terminal()
    total = 6
    print()
    words = [paint("Welcome to Chaser.", "head"), *(paint(line, "dim") for line in INTRO), "",
             "Setup takes a couple of minutes: a check of this computer,",
             "where Chaser keeps its work, how it thinks, your name on",
             "approvals and the keys that stop it. Change any of it later",
             "with " + paint("chaser setup", "teal") + "."]
    width = min(shutil.get_terminal_size((96, 30)).columns - 4, 92)
    title = terminal_theme.wordmark(colour=_colour, full=_full) + paint(f" setup · v{version()}", "dim")
    body = terminal_art.beside(words, _colour) if terminal_art.enabled(_colour) else words
    for line in (terminal_theme.box(body, width, title=title, colour=_colour, full=_full) if _colour else ["Chaser Agent setup", *words]):
        print("  " + line)
    advanced = False
    if interactive:
        print(f"\n  {paint('q', 'key')}  {paint('QuickStart', 'head')}  {paint('sensible defaults; asks only how Chaser thinks and your name', 'dim')}"
              f"\n  {paint('a', 'key')}  {paint('Advanced  ', 'head')}  {paint('also choose the folder, port and packs', 'dim')}")
        advanced = ask("QuickStart or Advanced? [Q/a]").lower().startswith("a")

    found = chaser_home.detect_chaseos()
    if found and found["data_dir"] != settings["data_dir"] and (args.use_chaseos or (interactive and not args.non_interactive and _offer_chaseos(found))):
        settings = chaser_home.save({key: found[key] for key in ("data_dir", "port", "packs", "memory_limit_mb")})
        print(f"  {paint('✓', 'ok')} Using this computer's ChaseOS setup for Chaser: its folder, port and packs")

    step(1, total, "Checking this computer")
    show_rows(setup_checks.run(settings, routes=_routes(settings))["rows"])

    step(2, total, "Where Chaser keeps its work")
    if interactive and advanced:
        folder = ask("Folder", settings["data_dir"])
        port = ask("Port", str(settings["port"]))
        packs = ask("Packs to load, separated by ;", ";".join(settings.get("packs") or []))
        settings = chaser_home.save({"data_dir": folder, "port": int(port) if port.isdecimal() else settings["port"],
                                     "packs": [p.strip() for p in packs.split(";") if p.strip()]})
    for line in setup_checks.fix(settings) or [f"{settings['data_dir']} is ready"]:
        print(f"  {paint('✓', 'ok')} {line}")

    step(3, total, "How Chaser thinks")
    if interactive:
        settings = step_power(settings)
    else:
        if args.provider:
            settings = chaser_home.save({"provider": providers.get(args.provider).id, "model": args.model or "",
                                         "base_url": args.base_url or ""})
        print(f"  {MARK['info']} Thinks with: {providers.describe(settings) if settings.get('provider') else 'not chosen (chaser model)'}")

    step(4, total, "Your name on approvals")
    if interactive:
        settings = step_name(settings)
    else:
        print(f"  {MARK['info']} {settings.get('reviewer') or 'Not set'}")

    step(5, total, "Keys that stop Chaser")
    show_shortcuts(settings)

    step(6, total, "Start Chaser")
    started = False
    if not args.no_start and (not interactive or confirm("Start Chaser now and open the HUD?")):
        started = step_start(settings, open_hud=interactive)
    else:
        running = setup_checks.gateway_health(int(settings["port"]))
        print(f"  {paint('✓', 'ok')} Already running on http://127.0.0.1:{settings['port']}/" if running
              else f"  {MARK['info']} Not started. Start it any time: chaser gateway")
        started = bool(running)
    from datetime import UTC, datetime

    settings = chaser_home.save({"onboarded_at": datetime.now(UTC).isoformat(timespec="seconds")})
    heading("Done. Try:")
    for command, words in (("chaser", "the home screen"), ("chaser chat", "talk to Chaser and watch it work"),
                           ("chaser open", "the HUD" + ("" if started else " (start Chaser first: chaser gateway)")),
                           ("chaser gateway install", "keep Chaser running whenever you're signed in"),
                           ("chaser help", "every command")):
        print(f"  {paint(f'{command:<24}', 'teal')}{paint(words, 'dim')}")
    return 0


def run_gateway(args: argparse.Namespace) -> int:
    settings = chaser_home.load()
    action = args.action
    if action == "run" or (action == "start" and args.foreground):
        if setup_checks.gateway_health(int(settings["port"])):
            print(f"Chaser is already running on port {settings['port']}.")
            return 0
        print(f"Chaser is running on http://127.0.0.1:{settings['port']}/ and restarts itself if it stops. Ctrl+C to stop.")
        try:
            gateway_service.supervise(settings)
        except KeyboardInterrupt:
            pass
        return 0
    if action == "install":
        try:
            command = gateway_service.install()
        except OSError as exc:
            print(f"{MARK['fail']} {exc}")
            return 1
        print(f"{MARK['ok']} Chaser now starts whenever you sign in to Windows, and restarts itself if it stops.")
        print(paint(f"  Runs: {command}", "dim"))
        print(paint("  Turn it off with: chaser gateway uninstall", "dim"))
        ok, message = gateway_start(settings)
        print(message)
        return 0 if ok else 1
    if action == "uninstall":
        print(f"{MARK['ok']} Chaser no longer starts at sign-in." if gateway_service.uninstall() else "Chaser wasn't set to start at sign-in.")
        print(paint("  It's still running now if it was. Stop it with: chaser gateway stop", "dim"))
        return 0
    if action in {"start", "restart"}:
        if action == "restart":
            ok, message = gateway_stop(settings)
            print(message)
            if not ok:
                return 1
        ok, message = gateway_start(settings)
        print(message)
        if ok and args.open:
            from chaser_agent import agent_cli

            agent_cli.run_open(argparse.Namespace(data_dir=str(settings["data_dir"]), port=int(settings["port"])))
        return 0 if ok else 1
    if action == "stop":
        ok, message = gateway_stop(settings)
        print(message)
        return 0 if ok else 1
    if action == "status":
        row = next(item for item in setup_checks.run(settings)["rows"] if item["id"] == "gateway")
        print(f"{MARK[row['state']]} {row['detail']}")
        if _running(settings):
            status, reply = _service_call(settings, "GET", "/v1/agent/status")
            if status == 200 and not (reply.get("reasoners") or {}).get("routes"):
                time.sleep(2)  # routes are checked in the background the first time anyone asks
                status, reply = _service_call(settings, "GET", "/v1/agent/status")
            if status == 200:
                for route in (reply.get("reasoners") or {}).get("routes") or []:
                    state = "ready" if route.get("available") and route.get("connected", True) is not False else (route.get("reason") or "not available")
                    print(f"  {route.get('label')}: {state}")
                print(f"  Sessions: {reply.get('sessions', 0)}, running {len(reply.get('active_sessions') or [])}, waiting for you {len(reply.get('waiting_for_operator') or [])}")
        print(f"  Starts at sign-in: {'yes' if gateway_service.installed() else 'no (chaser gateway install)'}")
        return 0
    if action == "logs":
        log = Path(settings["data_dir"]) / "service.log"
        if args.follow:
            print(paint(f"Following {log} and its error log. Ctrl+C to stop.", "dim"))
            try:
                gateway_service.follow([log, Path(str(log) + ".err")], lines=args.lines)
            except KeyboardInterrupt:
                pass
            return 0
        for path in (log, Path(str(log) + ".err")):
            if path.is_file():
                print(paint(f"— {path.name}", "dim"))
                print("\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-args.lines:]))
        return 0
    return 2


def run_doctor(args: argparse.Namespace) -> int:
    settings = chaser_home.load()
    if args.fix:
        for line in setup_checks.fix(settings):
            print(f"{MARK['ok']} {line}")
    report = setup_checks.run(settings, online=args.online, routes=_routes(settings))
    if args.json:
        print(json.dumps(report, indent=1, ensure_ascii=False))
    else:
        heading("Chaser pre-flight" + (" (key checked online)" if args.online else ""))
        show_rows(report["rows"])
        verdict = {"ok": "Ready.", "warn": "Chaser can run; the items marked ! are worth fixing.", "fail": "Fix the items marked ✗ first."}[report["result"]]
        print("\n" + paint(verdict, report["result"]))
    return 1 if report["result"] == "fail" else 0


def run_key(args: argparse.Namespace) -> int:
    settings = chaser_home.load()
    if args.action == "add":
        return 0 if add_key(settings) else 1
    if args.action == "remove":
        if _running(settings):
            status, reply = _service_call(settings, "POST", "/v1/agent/setup/key/remove", {})
            removed = status == 200 and reply.get("removed")
        else:
            removed = cloud_key.forget()
        print("Removed the saved ChaseOS Cloud key." if removed else "No ChaseOS Cloud key is saved.")
        return 0
    found = cloud_key.describe()
    words = {"environment": "Given by your vault for this session", "saved": "Saved for this Windows account only", "none": "Not added"}
    print(f"ChaseOS Cloud key: {words[found['source']]}" + (" (saved, but this account can't decrypt it)" if found["saved"] and not found["readable"] else ""))
    if args.action in ("check", None) and found["source"] != "none":   # plain `chaser key` checks too: it is free
        result = cloud_key.check(os.environ.get("CHASEOS_CLOUD_KEY") or cloud_key.load())
        _say_check(result, saved=False)
        return 0 if result["ok"] else 1
    # Plain `chaser key` with nothing saved (Chase, 12 Nov: "Not added keeps appearing, fix that"): offer to add one
    # here instead of only reporting it. Only in a real terminal, so scripts still get a plain status line.
    if args.action is None and found["source"] == "none" and interactive_terminal():
        if confirm("Add a ChaseOS Cloud key now?"):
            return 0 if add_key(settings) else 1
        print("Add one any time: chaser key add")
    return 0


def run_shortcuts(args: argparse.Namespace) -> int:
    settings = chaser_home.load()
    if args.action == "set":
        try:
            chord = shortcuts.check_choice(args.name, args.chord, settings["shortcuts"])
        except ValueError as exc:
            print(f"{MARK['fail']} {exc}")
            return 1
        settings = chaser_home.save({"shortcuts": {args.name: chord}})
        print(f"{MARK['ok']} {shortcuts.NAMES[args.name]}: {chord}")
    elif args.action == "reset":
        settings = chaser_home.save({"shortcuts": dict(chaser_home.DEFAULT_SHORTCUTS)})
        print(f"{MARK['ok']} Back to the standard keys.")
    heading("Keys that stop Chaser")
    show_shortcuts(settings)
    return 0



def run_setup(args: argparse.Namespace) -> int:
    if not interactive_terminal():
        print("chaser setup needs a terminal. Use chaser key, chaser shortcuts or chaser onboard --non-interactive instead.")
        return 2
    sections = {"key": "1", "folder": "2", "name": "3", "packs": "4", "shortcuts": "5", "checks": "6", "gateway": "7"}
    choice = sections.get(args.section or "", "")
    while True:
        settings = chaser_home.load()
        if not choice:
            found = cloud_key.describe()
            running = _running(settings)
            key_text = {"environment": "from your vault", "saved": "saved", "none": "not added"}[found["source"]]
            stop = shortcuts.label(settings["shortcuts"]["stop"]) if settings["shortcuts"].get("stop") else "not set"
            items = [terminal_ui.Item("1", "ChaseOS Cloud key", key_text), terminal_ui.Item("2", "Where Chaser keeps its work", settings["data_dir"]),
                     terminal_ui.Item("3", "Your name on approvals", settings.get("reviewer") or "not set"),
                     terminal_ui.Item("4", "Packs", f"{len(settings.get('packs') or [])} loaded at start"), terminal_ui.Item("5", "Shortcuts", f"Stop {stop}"),
                     terminal_ui.Item("6", "Run the checks"), terminal_ui.Item("7", "Stop Chaser" if running else "Start Chaser")]
            status = paint(f"running on 127.0.0.1:{settings['port']}", "ok") if running else paint("not running", "dim")
            choice = terminal_ui.select("Chaser · settings", items, header=[status], paint=paint) or "q"
            print("\033[2J\033[H", end="")
        if choice in {"q", "quit", ""}:
            return 0
        if choice == "1":
            step_key(settings, offer=False) if cloud_key.describe()["source"] != "none" else add_key(settings)
        elif choice == "2":
            folder = ask("Folder", settings["data_dir"])
            port = ask("Port", str(settings["port"]))
            chaser_home.save({"data_dir": folder, "port": int(port) if port.isdecimal() else settings["port"]})
            print(paint("  Saved. Restart Chaser to use it: chaser gateway restart", "dim"))
        elif choice == "3":
            step_name(settings)
        elif choice == "4":
            packs = ask("Packs to load, separated by ;", ";".join(settings.get("packs") or []))
            chaser_home.save({"packs": [p.strip() for p in packs.split(";") if p.strip()]})
            print(paint("  Saved. Restart Chaser to load them: chaser gateway restart", "dim"))
        elif choice == "5":
            show_shortcuts(settings)
            name = ask("Change which? stop, stop_fallback, take_over (Enter to keep)")
            if name in shortcuts.NAMES:
                try:
                    chord = shortcuts.check_choice(name, ask("New keys, e.g. Ctrl+Alt+Shift+X"), settings["shortcuts"])
                    chaser_home.save({"shortcuts": {name: chord}})
                    print(f"  {paint('✓', 'ok')} {shortcuts.NAMES[name]}: {chord}")
                except ValueError as exc:
                    print(f"  {paint('✗', 'fail')} {exc}")
        elif choice == "6":
            show_rows(setup_checks.run(settings, online=True, routes=_routes(settings))["rows"])
        elif choice == "7":
            if _running(settings):
                print("  " + gateway_stop(settings)[1])
            else:
                step_start(settings)
        if args.section:
            return 0
        terminal_ui.pause(paint)
        choice = ""


def version() -> str:
    try:
        from importlib.metadata import version as installed

        return installed("chaser-agent")
    except Exception:  # running from a checkout that isn't installed
        return "dev"


def _greeting(settings: dict[str, Any]) -> str:
    hour = time.localtime().tm_hour
    part = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening"
    name = (settings.get("reviewer") or "").split(" ")[0]
    return f"Good {part}{', ' + name if name else ''}."


def _status_lines(settings: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """The home screen's facts as label/value rows: running, model, what's waiting, who signs. Only what's real."""
    facts: dict[str, Any] = {"running": _running(settings), "waiting": [], "routes": []}
    if facts["running"]:
        status, reply = _service_call(settings, "GET", "/v1/agent/status")
        if status == 200:
            facts["waiting"] = reply.get("waiting_for_operator") or []
            facts["routes"] = (reply.get("reasoners") or {}).get("routes") or []
    provider = providers.get(settings.get("provider"))
    route = next((r for r in facts["routes"] if r.get("id") == provider.id), None)
    working = next((r for r in facts["routes"] if r.get("id") != "bridge" and r.get("available")), None)
    if not settings.get("provider") and working:
        shown = f"{working.get('label')} · {working['model']}" if working.get("model") and working.get("id") != "claude-cli" else working.get("label")
        model = paint(shown, "text") + paint("  · auto", "dim")
    elif not settings.get("provider"):
        model = paint("not chosen yet", "warn") + paint("  · press m", "dim")
    elif route is not None and not (route.get("available") and route.get("connected", True) is not False):
        model = paint(providers.describe(settings), "text") + paint("  · " + (route.get("reason") or "not available"), "warn")
    else:
        model = paint(providers.describe(settings), "text")
    if facts["running"]:
        state = paint("●", "ok") + paint(f" Running", "text") + paint(f"  127.0.0.1:{settings['port']}", "dim")
        if gateway_service.installed():
            state += paint("  · starts at sign-in", "dim")
    else:
        state = paint("○", "dim") + paint(" Stopped", "text") + paint("  · press g to start", "dim")
    waiting = len(facts["waiting"])
    waits = paint(f"{waiting} for you", "warn") if waiting else paint("nothing for you", "dim")
    reviewer = settings.get("reviewer")
    signs = paint(reviewer, "text") if reviewer else paint("no name yet", "warn") + paint("  · Settings", "dim")
    rows = [("Chaser", state), ("Model", model), ("Waiting", waits), ("Signs as", signs)]
    return [paint(f"{label:<10}", "dim") + value for label, value in rows], facts


def home_header(settings: dict[str, Any], status: list[str]) -> list[str]:
    """The framed card at the top of `chaser`: Chaser on the left, a greeting and the facts on the right."""
    words = [paint(_greeting(settings), "head"), *(paint(line, "dim") for line in INTRO), "", *status]
    width = min(shutil.get_terminal_size((96, 30)).columns - 4, 92)
    title = terminal_theme.wordmark(colour=_colour, full=_full) + paint(f" v{version()}", "dim")
    if terminal_art.enabled(_colour):
        inner = terminal_art.beside(words, _colour)
        roomy = shutil.get_terminal_size((96, 44)).lines >= 40
        return terminal_theme.box(["", *inner, ""] if roomy else inner, width, title=title, colour=_colour, full=_full)
    if _colour:
        return terminal_theme.box(words, width, title=title, colour=_colour, full=_full)
    return ["Chaser Agent v" + version(), *words]


def run_home(_: argparse.Namespace) -> int:
    settings = chaser_home.load()
    if not settings.get("onboarded_at"):
        print("Chaser isn't set up on this computer yet.")
        if interactive_terminal() and confirm("Set it up now?"):
            return run_onboard(argparse.Namespace(reset=False, data_dir=None, port=None, reviewer=None, pack=[], non_interactive=False,
                                                  no_start=False, use_chaseos=False, provider=None, model=None, base_url=None))
        print("Run: chaser onboard")
        return 0
    if not interactive_terminal():
        report = setup_checks.run(settings, routes=_routes(settings))
        heading("Chaser Agent")
        show_rows([item for item in report["rows"] if item["id"] in {"gateway", "routes", "cloud_key", "reviewer"}])
        print("\n  " + "   ".join(paint(c, "teal") for c in ("chaser chat", "chaser open", "chaser gateway", "chaser setup", "chaser doctor")))
        return 0
    from chaser_agent import agent_cli, chaser_chat

    last = "c"
    while True:
        settings = chaser_home.load()
        status, facts = _status_lines(settings)
        running = facts["running"]
        header = home_header(settings, status)
        items = [terminal_ui.Item("c", "Chat with Chaser", "" if running else "starts Chaser first", "Work"),
                 terminal_ui.Item("w", "Waiting for you", str(len(facts["waiting"])) if facts["waiting"] else "", "Work"),
                 terminal_ui.Item("r", "Recent work", "", "Work"),
                 terminal_ui.Item("h", "Open the HUD", "", "Work"),
                 terminal_ui.Item("g", "Stop Chaser" if running else "Start Chaser", "", "Chaser"),
                 terminal_ui.Item("a", "Start at sign-in", "on" if gateway_service.installed() else "off", "Chaser"),
                 terminal_ui.Item("l", "Logs", "live", "Chaser"),
                 terminal_ui.Item("m", "Model", providers.get(settings.get("provider")).label if settings.get("provider") else "auto", "Set up"),
                 terminal_ui.Item("t", "Channels", ", ".join(channels.PLATFORMS[c]["label"] for c in channels.configured(settings)) or "not set up", "Set up"),
                 terminal_ui.Item("s", "Settings", "key · folder · name · packs · shortcuts", "Set up"),
                 terminal_ui.Item("d", "Checks", "", "Set up"),
                 terminal_ui.Item("q", "Quit", "Chaser keeps running", "Set up")]
        choice = terminal_ui.select("", items, header=header, paint=paint, start=last,
                                    footer="↑↓ move   enter open   a–z jump   ? all commands   q quit")
        print("\033[2J\033[H", end="")
        if choice in (None, "q"):
            return 0
        last = choice
        try:
            if choice == "?":
                print_help()
                terminal_ui.pause(paint)
                continue
            if choice == "m":
                choose_model(settings)
                terminal_ui.pause(paint)
                continue
            if choice == "t":
                run_channels(argparse.Namespace(action="list", platform=None))
                pick = ask("Add or change one? telegram, discord, slack, email (Enter to go back)").lower()
                if pick in channels.PLATFORMS:
                    add_channel(pick)
                terminal_ui.pause(paint)
                continue
            if choice in {"c", "w", "r"}:
                if not running and not step_start(settings, open_hud=False):
                    terminal_ui.pause(paint)
                    continue
                chat = chaser_chat.Chat(settings, paint)
                if choice == "c":
                    chat.run()
                    continue
                chat.say(paint("  Chaser · " + ("waiting for you" if choice == "w" else "recent work"), "head"))
                chat.command("/waiting" if choice == "w" else "/sessions")
                if chat.session:
                    chat.run()
                    continue
            elif choice == "h":
                if running or step_start(settings, open_hud=False):
                    agent_cli.run_open(argparse.Namespace(data_dir=str(settings["data_dir"]), port=int(settings["port"])))
            elif choice == "g":
                print("  " + (gateway_stop(settings)[1] if running else gateway_start(settings)[1]))
            elif choice == "a":
                if gateway_service.installed():
                    gateway_service.uninstall()
                    print(f"  {MARK['ok']} Chaser no longer starts at sign-in.")
                elif confirm("Start Chaser whenever you sign in to Windows, restarting it if it stops?"):
                    gateway_service.install()
                    print(f"  {MARK['ok']} Chaser now starts at sign-in.")
                    if not running:
                        print("  " + gateway_start(settings)[1])
            elif choice == "s":
                run_setup(argparse.Namespace(section=None))
                continue
            elif choice == "d":
                heading("Chaser pre-flight (key checked online)")
                show_rows(setup_checks.run(settings, online=True, routes=_routes(settings))["rows"])
            elif choice == "l":
                log = Path(settings["data_dir"]) / "service.log"
                print(paint(f"  Following {log}. Ctrl+C to go back.", "dim"))
                gateway_service.follow([log, Path(str(log) + ".err")], lines=30)
        except KeyboardInterrupt:
            print()
        terminal_ui.pause(paint)


HELP = (
    ("Start", (("chaser", "the home screen"), ("chaser onboard", "first-run setup"),
               ("chaser chat [message]", "talk to Chaser; --image FILE, --mode plan|bypass"), ("chaser ask \"task\"", "give Chaser a task and follow it"),
               ("chaser open", "the HUD"))),
    ("Run", (("chaser gateway", "start Chaser in the background (stop, restart, run)"),
             ("chaser gateway install", "start at sign-in (uninstall to stop)"), ("chaser status", "running, model, routes, what's waiting"),
             ("chaser logs [-f]", "the service log"))),
    ("Work", (("chaser waiting", "what needs your answer or your yes"), ("chaser sessions", "recent work and where each stands"),
              ("chaser stop", "stop every task now; the kill switch"),
              ("chaser approve [SESSION]", "say yes, signed with your name"), ("chaser reject [SESSION]", "say no, signed with your name"),
              ("chaser receipt [SESSION]", "check the hash chain; who approved what; what it wrote"))),
    ("Set up", (("chaser model", "choose the AI provider and model"), ("chaser channels", "Telegram, Discord, Slack, email; owner-only (add, test, remove)"), ("chaser voice", "speak to Chaser, offline"), ("chaser key", "the ChaseOS Cloud key"),
                ("chaser setup [section]", "every setting from a menu"), ("chaser shortcuts", "the stop and take-over keys"),
                ("chaser doctor [--online] [--fix]", "pre-flight checks"))),
    ("Help", (("chaser help [command]", "this, or one command's options"), ("chaser version", "the installed version"))),
)


def print_help(command: str | None = None) -> int:
    if command:
        parser = build_parser()
        for action in parser._subparsers._group_actions:  # noqa: SLF001 - argparse keeps subcommands here
            if command in action.choices:
                action.choices[command].print_help()
                return 0
        print(f"No command called {command}. Run: chaser help")
        return 2
    print()
    print("  " + terminal_theme.wordmark(colour=_colour, full=_full) + paint(f"  v{version()}", "dim"))
    print("  " + paint(" ".join(INTRO), "dim"))
    width = max(len(command) for _, rows in HELP for command, _ in rows) + 3
    for group, rows in HELP:
        print("\n  " + paint(group.upper(), "dim"))
        for command, words in rows:
            print(f"    {paint(f'{command:<{width}}', 'teal')}{words}")
    print("\n  " + paint("Settings live in " + str(chaser_home.settings_path()) + ". NO_COLOR or CHASER_NO_ART turn off colour or art.", "dim"))
    return 0


def run_model(args: argparse.Namespace) -> int:
    settings = chaser_home.load()
    if args.action == "list":
        for provider in providers.CATALOGUE:
            mark = paint("●", "ok") if provider.id == settings.get("provider") else " "
            print(f"  {mark} {provider.id:<14} {provider.label:<36} {paint(provider.blurb, 'dim')}")
        return 0
    if args.action == "set":
        if not args.provider:
            print("chaser model set PROVIDER [--model NAME] [--base-url URL]   (see: chaser model list)")
            return 2
        provider = providers.get(args.provider)
        settings = chaser_home.save({"provider": provider.id, "model": args.model or "", "base_url": args.base_url or ""})
        print(f"{MARK['ok']} Chaser thinks with {providers.describe(settings)}. Restart to use it: chaser gateway restart")
        return 0
    if args.action == "show" or not interactive_terminal():
        print(f"Thinks with: {providers.describe(settings) if settings.get('provider') else 'not chosen yet'}")
        provider = providers.get(settings.get("provider"))
        if provider.needs_key and provider.kind == "openai":
            print(f"Key: {providers.load_key(provider.id)[1]}")
        if not interactive_terminal():
            print("Change it: chaser model (in a terminal), or chaser model set PROVIDER --model NAME")
        return 0
    choose_model(settings)
    return 0


# --- The work and its proof -----------------------------------------------------

def _need_running(settings: dict[str, Any]) -> bool:
    if _running(settings):
        return True
    print("Chaser isn't running. Start it with: chaser gateway")
    return False


def _waiting_details(settings: dict[str, Any]) -> list[dict[str, Any]]:
    _, value = _service_call(settings, "GET", "/v1/agent/sessions")
    details = []
    for row in (value or {}).get("sessions") or []:
        if row.get("status") in chaser_work.WAITING:
            status, snap = _service_call(settings, "GET", f"/v1/agent/sessions/{row['id']}")
            if status == 200 and snap.get("pending"):
                details.append(snap)
    return details


def run_waiting(_: argparse.Namespace) -> int:
    settings = chaser_home.load()
    if not _need_running(settings):
        return 1
    for line in chaser_work.waiting_lines(_waiting_details(settings), paint):
        print(line)
    return 0


def run_sessions(args: argparse.Namespace) -> int:
    settings = chaser_home.load()
    if not _need_running(settings):
        return 1
    _, value = _service_call(settings, "GET", "/v1/agent/sessions")
    for line in chaser_work.sessions_table((value or {}).get("sessions") or [], paint, limit=args.limit):
        print(line)
    return 0


def run_decision(args: argparse.Namespace) -> int:
    """`chaser approve` / `chaser reject`: show the exact request, then sign the decision with your name."""
    settings = chaser_home.load()
    if not _need_running(settings):
        return 1
    decision = args.decision
    waiting = [s for s in _waiting_details(settings) if (s.get("pending") or {}).get("kind") == "approval"]
    if args.session:
        snap = next((s for s in waiting if s["id"] == args.session or s["id"].startswith(args.session)), None)
    elif len(waiting) == 1:
        snap = waiting[0]
    else:
        print("Nothing is waiting for your yes." if not waiting else "Several approvals are waiting; name one:")
        for line in chaser_work.waiting_lines(waiting, paint)[:12]:
            print(line)
        return 3 if not waiting else 2
    if snap is None:
        print("That session isn't waiting for an approval. See: chaser waiting")
        return 3
    pending = snap["pending"]
    print(paint(f"  {snap.get('title')}", "head"))
    print(f"  wants to run {paint(str(pending.get('tool')), 'head')} with:")
    for line in json.dumps(pending.get("args") or {}, ensure_ascii=False, indent=1).splitlines()[:30]:
        print(paint("    " + line, "dim"))
    print(paint(f"  digest {pending.get('digest')}", "dim"))
    reviewer = (settings.get("reviewer") or "").strip()
    signer = f"{reviewer} (terminal)" if reviewer else "local_operator"
    word = "Approve" if decision == "approve" else "Reject"
    if not args.yes and not (interactive_terminal() and confirm(f"{word} this, signed {signer}?", default=decision == "reject")):
        print("Left waiting. Nothing was decided.")
        return 0
    status, value = _service_call(settings, "POST", f"/v1/agent/sessions/{snap['id']}/approvals",
                                  {"approval_id": pending["id"], "digest": pending["digest"], "decision": decision, "decided_by": signer})
    if status != 202:
        print(f"{MARK['fail']} {((value or {}).get('error') or {}).get('message') or 'Chaser did not accept that.'}")
        return 2
    print(f"{paint(MARK['ok'], 'ok')} {'Approved' if decision == 'approve' else 'Rejected'}, signed {signer}. It's in the session's receipt.")
    return 0


def run_stop_all(_: argparse.Namespace) -> int:
    """`chaser stop`: stop every task now. The service keeps running; nothing is deleted."""
    settings = chaser_home.load()
    if not _need_running(settings):
        return 1
    stopped = chaser_work.stop_everything(lambda method, route, body=None: _service_call(settings, method, route, body))
    print(f"{paint(MARK['ok'], 'ok')} Stopped {len(stopped)} task(s). Chaser is still running; stop it too with: chaser gateway stop"
          if stopped else "Nothing was running.")
    return 0


def run_receipt(args: argparse.Namespace) -> int:
    settings = chaser_home.load()
    folder = chaser_work.find_session(Path(settings["data_dir"]), args.session)
    if folder is None:
        print("No session found" + (f" matching {args.session}." if args.session else " yet.") + " See: chaser sessions")
        return 3
    value = chaser_work.receipt(folder)
    if args.json:
        print(json.dumps(value, indent=1, ensure_ascii=False))
    else:
        for line in chaser_work.receipt_lines(value, paint):
            print(line)
    return 0 if value["chain"].get("verified") else 4


# --- Messaging channels ------------------------------------------------------------

def _restart_offer(settings: dict[str, Any]) -> None:
    if _running(settings) and interactive_terminal() and confirm("Restart Chaser so the channel starts now?"):
        print("  " + gateway_stop(settings)[1])
        print("  " + gateway_start(settings)[1])
    elif not _running(settings):
        print(paint("  It starts with Chaser: chaser gateway", "dim"))


def add_channel(platform: str) -> int:
    settings = chaser_home.load()
    info = channels.PLATFORMS[platform]
    print(paint(f"  {info['label']}", "head") + paint("  only the accounts you allow can talk to Chaser; approvals still need your yes", "dim"))
    print(paint(f"  {info['where']} The token won't show as you paste it.", "dim"))
    if platform == "email":
        return add_email_channel(settings)
    try:
        token = cloud_key.validate(secret_input(f"  {info['label']} bot token: "))
    except (ValueError, SecretInputUnavailable) as exc:
        print(f"  {paint('✗', 'fail')} {exc}")
        return 2
    except (EOFError, KeyboardInterrupt):
        print()
        return 1
    if platform == "telegram":
        bot = channels.Telegram(token)
        ok, name = bot.whoami()
        if not ok:
            print(f"  {paint('✗', 'fail')} {name}")
            return 2
        print(f"  {paint('✓', 'ok')} Connected to {name}. Now send it any message from your own Telegram account (waiting up to 2 minutes)…")
        found = None
        deadline = time.monotonic() + 120
        while found is None and time.monotonic() < deadline:
            found = next(iter(bot.poll(wait=20)), None)
        if found is None:
            print(f"  {paint('!', 'warn')} No message arrived. Run chaser channels add telegram again when you're ready.")
            return 1
        if not confirm(f"Allow {found.name or 'this account'} (id {found.user}) to talk to Chaser?"):
            return 1
        allow = [found.user]
        greet = lambda: bot.send(found.chat, "Chaser is connected. Only you can talk to it here; it will ask before anything leaves your computer.")  # noqa: E731
    elif platform == "slack":
        bot = channels.Slack(token, [])
        ok, name = bot.whoami()
        if not ok:
            print(f"  {paint('✗', 'fail')} {name}")
            return 2
        print(f"  {paint('✓', 'ok')} Connected as {name}.")
        print(paint("  Your member ID: in Slack, click your name → Profile → ⋮ → Copy member ID.", "dim"))
        user = ask("Your Slack member ID").strip().upper()
        if not (user.startswith(("U", "W")) and user[1:].isalnum()):
            print(f"  {paint('✗', 'fail')} That isn't a Slack member ID (it starts with U).")
            return 2
        allow = [user]
        bot.allow = allow
        greet = lambda: bot.greet(user, "Chaser is connected. Only you can talk to it here; it will ask before anything leaves your computer.")  # noqa: E731
    else:
        bot = channels.Discord(token, [])
        ok, name = bot.whoami()
        if not ok:
            print(f"  {paint('✗', 'fail')} {name}")
            return 2
        print(f"  {paint('✓', 'ok')} Connected as {name}.")
        print(paint(f"  Invite it to a server you're in, if you haven't: https://discord.com/oauth2/authorize?client_id={bot.me}&scope=bot&permissions=0", "dim"))
        print(paint("  Your user ID: Discord Settings → Advanced → Developer Mode on, then right-click your name → Copy User ID.", "dim"))
        user = ask("Your Discord user ID").strip()
        if not user.isdecimal():
            print(f"  {paint('✗', 'fail')} That isn't a Discord user ID (it's a long number).")
            return 2
        allow = [user]
        bot.allow = allow
        greet = lambda: bot.greet(user, "Chaser is connected. Only you can talk to it here; it will ask before anything leaves your computer.")  # noqa: E731
    try:
        channels.save_token(platform, token)
    except cloud_key.KeyStoreUnavailable as exc:
        print(f"  {paint('✗', 'fail')} {exc}")
        return 2
    chosen = dict(settings.get("channels") or {})
    chosen[platform] = {"enabled": True, "allow": allow}
    settings = chaser_home.save({"channels": chosen})
    print(f"  {paint('✓', 'ok')} {info['label']} is set up; the token is saved encrypted for this Windows account."
          if greet() is not False else f"  {paint('!', 'warn')} Saved, but the hello didn't arrive; check the bot shares a server with you.")
    _restart_offer(settings)
    return 0


MAIL_HOSTS = {"gmail.com": ("imap.gmail.com", "smtp.gmail.com"), "googlemail.com": ("imap.gmail.com", "smtp.gmail.com"),
              "outlook.com": ("outlook.office365.com", "smtp.office365.com"), "hotmail.com": ("outlook.office365.com", "smtp.office365.com"),
              "icloud.com": ("imap.mail.me.com", "smtp.mail.me.com"), "me.com": ("imap.mail.me.com", "smtp.mail.me.com")}


def add_email_channel(settings: dict[str, Any]) -> int:
    """An inbox Chaser reads and answers. Best as an address of its own; only vouched-for allowed senders count."""
    print(paint("  Best with an address just for Chaser. It answers only the senders you allow, and only when their", "dim"))
    print(paint("  mail server vouches for them (DKIM or SPF), because a From line alone can be forged.", "dim"))
    address = ask("Chaser's email address").strip()
    if "@" not in address:
        return 2
    imap, smtp = MAIL_HOSTS.get(address.rsplit("@", 1)[1].lower(), ("", ""))
    imap, smtp = ask("IMAP server", imap), ask("SMTP server (SSL, port 465)", smtp)
    try:
        password = cloud_key.validate(secret_input("  App password: "))
    except (ValueError, EOFError, KeyboardInterrupt) as exc:
        print(f"  {paint('✗', 'fail')} {exc}" if isinstance(exc, ValueError) else "")
        return 2
    allow = [a.strip().lower() for a in ask("Senders allowed to instruct Chaser, separated by commas").split(",") if "@" in a]
    if not allow:
        print(f"  {paint('✗', 'fail')} Allow at least one sender.")
        return 2
    config = {"enabled": True, "allow": allow, "address": address, "imap_host": imap, "smtp_host": smtp}
    ok, name = channels.Email(password, config, allow).whoami()
    if not ok:
        print(f"  {paint('✗', 'fail')} {name}")
        return 2
    channels.save_token("email", password)
    chosen = dict(settings.get("channels") or {})
    chosen["email"] = config
    settings = chaser_home.save({"channels": chosen})
    print(f"  {paint('✓', 'ok')} Signed in to {name}. Chaser will answer mail from {', '.join(allow)}; the password is saved encrypted.")
    _restart_offer(settings)
    return 0


def run_voice(args: argparse.Namespace) -> int:
    from chaser_agent import chaser_inputs

    settings = chaser_home.load()
    if args.action == "set":
        if not args.folder:
            print("chaser voice set MODEL_FOLDER   (a pinned faster-whisper model with its stt-model.json)")
            return 2
        settings = chaser_home.save({"voice_model_dir": str(Path(args.folder).resolve())})
    ready, why = chaser_inputs.voice_ready(settings)
    print(f"{paint(MARK['ok'], 'ok')} Voice is ready: {why}. Use /voice in chaser chat." if ready else f"{paint('!', 'warn')} {why}")
    return 0 if ready else 1


def run_channels(args: argparse.Namespace) -> int:
    settings = chaser_home.load()
    chosen = settings.get("channels") or {}
    if args.action == "list":
        print()
        heading("Messaging channels")
        for platform, info in channels.PLATFORMS.items():
            value = chosen.get(platform)
            if value and channels.load_token(platform):
                state = paint("● connected", "ok") + paint(f"  {len(value.get('allow') or [])} allowed account(s)", "dim")
            elif value:
                state = paint("! no token", "warn") + paint(f"  chaser channels add {platform}", "dim")
            else:
                state = paint("○ not set up", "dim") + paint(f"  chaser channels add {platform}", "dim")
            print(f"    {info['label']:<10} {state}")
        print(paint("\n  Only allowed accounts are heard. Every approval still needs a yes, signed by name into the receipt.", "dim"))
        print(paint("  Next: WhatsApp (official Cloud API), Signal, Microsoft Teams, Matrix.", "dim"))
        return 0
    if not args.platform:
        print(f"chaser channels {args.action} {'|'.join(channels.PLATFORMS)}")
        return 2
    if args.action == "add":
        if not interactive_terminal():
            print("chaser channels add needs a terminal.")
            return 2
        return add_channel(args.platform)
    if args.action == "remove":
        channels.forget_token(args.platform)
        chosen = {k: v for k, v in chosen.items() if k != args.platform}
        chaser_home.save({"channels": chosen})
        print(f"{MARK['ok']} {channels.PLATFORMS[args.platform]['label']} removed; its token is deleted. Restart Chaser to stop it listening.")
        return 0
    if args.action == "test":
        value = chosen.get(args.platform)
        if not value:
            print(f"Not set up. Run: chaser channels add {args.platform}")
            return 3
        adapter = channels.adapter_for(args.platform, settings, {})
        ok, name = adapter.whoami()
        if not ok:
            print(f"{MARK['fail']} {name}")
            return 2
        for user in value.get("allow") or []:
            if args.platform in {"telegram", "email"}:
                adapter.send(user, "A test from chaser channels test.")
            else:
                adapter.greet(user, "A test from chaser channels test.")
        print(f"{MARK['ok']} Sent a test to {len(value.get('allow') or [])} account(s) from {name}.")
        return 0
    if args.action == "run":
        if not channels.configured(settings):
            print("No channels set up. Run: chaser channels add telegram (or discord)")
            return 3
        print(paint("Serving the channels in this terminal. Ctrl+C to stop.", "dim"))
        try:
            channels.run(settings, channels.service_caller(settings))
        except KeyboardInterrupt:
            pass
        return 0
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chaser", description="Set up, start and check Chaser Agent. Run chaser help for every command.",
                                     formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n")[1])
    sub = parser.add_subparsers(dest="command")
    onboard = sub.add_parser("onboard", help="First-run setup: checks, folder, key, your name, shortcuts, start.")
    onboard.add_argument("--non-interactive", action="store_true", help="Use flags and defaults; ask nothing. A key comes only from CHASEOS_CLOUD_KEY.")
    onboard.add_argument("--data-dir")
    onboard.add_argument("--port", type=int)
    onboard.add_argument("--reviewer", help="Your name on approvals.")
    onboard.add_argument("--pack", action="append", default=[], help="A pack to load at start. Repeatable.")
    onboard.add_argument("--no-start", action="store_true", help="Don't start Chaser at the end.")
    onboard.add_argument("--reset", action="store_true", help="Start from default settings. Work, receipts and the key are kept.")
    onboard.add_argument("--use-chaseos", action="store_true", help="Use this computer's ChaseOS setup for Chaser (folder, port, packs) if there is one.")
    onboard.add_argument("--provider", choices=sorted(providers.BY_ID), help="How Chaser thinks. The key comes from the provider's environment variable.")
    onboard.add_argument("--model")
    onboard.add_argument("--base-url", help="With --provider custom: the endpoint's address, up to /v1.")
    onboard.set_defaults(func=run_onboard)
    chat = sub.add_parser("chat", aliases=["tui"], help="Talk to Chaser and watch it work.")
    chat.add_argument("message", nargs="*", help="Start with this message.")
    chat.add_argument("--session", help="Carry on with this session.")
    chat.add_argument("--route", help="How new work thinks: auto or a route id from chaser status.")
    chat.add_argument("--image", action="append", default=[], help="Attach a picture to the first message. Repeatable.")
    chat.add_argument("--mode", choices=["ask", "plan", "bypass"], default="ask", help="How much Chaser may do without asking; bypass asks you to confirm.")
    chat.set_defaults(func=lambda args: __import__("chaser_agent.chaser_chat", fromlist=["run"]).run(args, paint))
    gateway = sub.add_parser("gateway", help="Start, stop or check Chaser's service.")
    gateway.add_argument("action", nargs="?", default="start", choices=["start", "stop", "restart", "status", "logs", "run", "install", "uninstall"])
    gateway.add_argument("--foreground", action="store_true", help="Run in this terminal instead of the background (same as run).")
    gateway.add_argument("-f", "--follow", action="store_true", help="With logs: keep printing new lines.")
    gateway.add_argument("--open", action="store_true", help="Open the HUD once it's running.")
    gateway.add_argument("--lines", type=int, default=40, help="Lines of log to show.")
    gateway.set_defaults(func=run_gateway)
    setup = sub.add_parser("setup", help="Change any setting from a menu.")
    setup.add_argument("section", nargs="?", choices=["key", "folder", "name", "packs", "shortcuts", "checks", "gateway"])
    setup.set_defaults(func=run_setup)
    doctor = sub.add_parser("doctor", help="Pre-flight checks.")
    doctor.add_argument("--online", action="store_true", help="Also check the key with ChaseOS Cloud (free: it reads the balance).")
    doctor.add_argument("--fix", action="store_true", help="Create the private data folder if it's missing.")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=run_doctor)
    key = sub.add_parser("key", help="The ChaseOS Cloud key: status, add, check, remove.")
    key.add_argument("action", nargs="?", default=None, choices=["status", "add", "check", "remove"])  # None: plain `chaser key`
    key.set_defaults(func=run_key)
    keys = sub.add_parser("shortcuts", help="The keys that stop Chaser or take over.")
    keys.add_argument("action", nargs="?", default="show", choices=["show", "set", "reset"])
    keys.add_argument("name", nargs="?", choices=list(shortcuts.NAMES))
    keys.add_argument("chord", nargs="?", help="For example Ctrl+Alt+Shift+X")
    keys.set_defaults(func=run_shortcuts)
    model = sub.add_parser("model", help="Choose the AI provider and model Chaser thinks with.")
    model.add_argument("action", nargs="?", default="choose", choices=["choose", "show", "list", "set"])
    model.add_argument("provider", nargs="?", choices=sorted(providers.BY_ID))
    model.add_argument("--model")
    model.add_argument("--base-url")
    model.set_defaults(func=run_model)
    status = sub.add_parser("status", help="Is Chaser running, how it thinks, what's waiting.")
    status.set_defaults(func=lambda _a: run_gateway(argparse.Namespace(action="status", foreground=False, follow=False, open=False, lines=40)))
    logs = sub.add_parser("logs", help="The service log.")
    logs.add_argument("-f", "--follow", action="store_true")
    logs.add_argument("--lines", type=int, default=40)
    logs.set_defaults(func=lambda a: run_gateway(argparse.Namespace(action="logs", foreground=False, follow=a.follow, open=False, lines=a.lines)))
    waiting = sub.add_parser("waiting", help="What needs your answer or your yes, oldest first.")
    waiting.set_defaults(func=run_waiting)
    recent = sub.add_parser("sessions", help="Recent work and where each one stands.")
    recent.add_argument("--limit", type=int, default=15)
    recent.set_defaults(func=run_sessions)
    for verb, words in (("approve", "Say yes to a waiting request, signed with your name."), ("reject", "Say no to a waiting request, signed with your name.")):
        decide = sub.add_parser(verb, help=words)
        decide.add_argument("session", nargs="?", help="Which session; leave out when only one is waiting.")
        decide.add_argument("--yes", action="store_true", help="Don't ask to confirm.")
        decide.set_defaults(func=run_decision, decision="approve" if verb == "approve" else "reject")
    halt = sub.add_parser("stop", help="Stop every task now (the kill switch). Chaser itself keeps running.")
    halt.set_defaults(func=run_stop_all)
    proof = sub.add_parser("receipt", help="Check a session's hash chain from disk and show who approved what.")
    proof.add_argument("session", nargs="?", help="A session id or its start; the newest when left out.")
    proof.add_argument("--json", action="store_true")
    proof.set_defaults(func=run_receipt)
    voice = sub.add_parser("voice", help="Speak to Chaser: transcribed on this computer, confirmed before sending.")
    voice.add_argument("action", nargs="?", default="status", choices=["status", "set"])
    voice.add_argument("folder", nargs="?")
    voice.set_defaults(func=run_voice)
    chan = sub.add_parser("channels", help="Talk to Chaser from Telegram, Discord, Slack or email, owner-only and approval-governed.")
    chan.add_argument("action", nargs="?", default="list", choices=["list", "add", "remove", "test", "run"])
    chan.add_argument("platform", nargs="?", choices=sorted(channels.PLATFORMS))
    chan.set_defaults(func=run_channels)
    helper = sub.add_parser("help", help="Every command, or one command's options.")
    helper.add_argument("topic", nargs="?")
    helper.set_defaults(func=lambda a: print_help(a.topic))
    shown = sub.add_parser("version", help="The installed version.")
    shown.set_defaults(func=lambda _a: print(f"chaser-agent {version()}") or 0)
    for name in sorted(PASS_THROUGH):
        sub.add_parser(name, help=f"chaser-agent {name}, using your settings' folder and port.", add_help=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    _setup_terminal()
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in PASS_THROUGH:
        settings = chaser_home.load()
        os.environ.setdefault("CHASER_AGENT_DATA_DIR", str(settings["data_dir"]))
        if "--port" not in argv and argv[0] != "reasoner":
            argv += ["--port", str(settings["port"])]
        from chaser_agent import cli

        return cli.main(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "shortcuts" and args.action == "set" and not (args.name and args.chord):
        parser.error("chaser shortcuts set NAME KEYS, for example: chaser shortcuts set stop Ctrl+Alt+Shift+X")
    if not hasattr(args, "func"):
        return run_home(args)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print()
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
