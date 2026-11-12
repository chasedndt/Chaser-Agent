"""`chaser`: set up, start and check Chaser Agent from a terminal.

    chaser                 what's set up, and what to run next
    chaser onboard         first-run setup: checks, folder, key, your name, shortcuts, start
    chaser gateway         start Chaser's service in the background (stop, restart, status, logs)
    chaser setup           change any setting from a menu
    chaser doctor          pre-flight checks (--online also checks the key, --fix creates the folder)
    chaser key             add, check or remove the ChaseOS Cloud key (never shown)
    chaser shortcuts       the keys that stop Chaser or take over
    chaser open            the HUD
    chaser ask "..."       give Chaser a task and follow it

Everything else `chaser-agent` does still works, and `chaser ask`, `open`, `decide` and `agent-status`
use the folder and port from your settings, so you never pass them.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from chaser_agent import chaser_home, cloud_key, setup_checks, shortcuts

PASS_THROUGH = {"ask", "open", "decide", "agent-status", "reasoner"}
PID_FILE = "gateway.pid"
MARK = {"ok": "✓", "warn": "!", "fail": "✗", "info": "·"}
COLOUR = {"ok": "32", "warn": "33", "fail": "31", "info": "90", "head": "1", "dim": "90", "teal": "36"}
_colour = False


# --- Output -------------------------------------------------------------------

def _setup_terminal() -> None:
    global _colour
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _colour = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
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
    return f"\033[{COLOUR[tone]}m{text}\033[0m" if _colour else text


def heading(text: str) -> None:
    print("\n" + paint(text, "head"))


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

def _source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def gateway_command(settings: dict[str, Any]) -> list[str]:
    command = [sys.executable, "-X", "utf8", "-m", "chaser_agent.cli", "serve", "--data-dir", str(settings["data_dir"]),
               "--port", str(settings["port"]), "--memory-limit-mb", str(settings.get("memory_limit_mb") or 0)]
    for pack in settings.get("packs") or []:
        command += ["--pack", str(pack)]
    return command


def _listening_pid(port: int) -> int | None:
    if os.name != "nt":
        return None
    done = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, timeout=20)
    for line in done.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[1] == f"127.0.0.1:{port}" and parts[3].upper() == "LISTENING":
            return int(parts[4])
    return None


def gateway_start(settings: dict[str, Any], *, wait: float = 60) -> tuple[bool, str]:
    port = int(settings["port"])
    health = setup_checks.gateway_health(port)
    if health and health.get("service") == "chaser-agent":
        return True, f"Chaser is already running on http://127.0.0.1:{port}/"
    if not setup_checks.port_free(port):
        return False, f"Another program is using port {port}. Choose another with: chaser setup"
    folder = Path(settings["data_dir"])
    if not folder.exists():
        setup_checks.make_private_folder(folder)
    log = folder / "service.log"
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONPATH": os.pathsep.join([str(_source_root()), os.environ.get("PYTHONPATH", "")]).rstrip(os.pathsep)}
    flags = (getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)) if os.name == "nt" else 0
    with open(log, "ab") as out, open(str(log) + ".err", "ab") as err:
        process = subprocess.Popen(gateway_command(settings), cwd=str(folder), env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                   creationflags=flags, start_new_session=os.name != "nt", close_fds=True)
    (folder / PID_FILE).write_text(str(process.pid), encoding="ascii")
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False, f"Chaser stopped as it started. See {log}.err"
        health = setup_checks.gateway_health(port, timeout=1)
        if health and health.get("service") == "chaser-agent":
            return True, f"Chaser is running on http://127.0.0.1:{port}/"
        time.sleep(0.5)
    return False, f"Chaser didn't answer within {int(wait)} seconds. See {log}.err"


def gateway_stop(settings: dict[str, Any]) -> tuple[bool, str]:
    port = int(settings["port"])
    health = setup_checks.gateway_health(port)
    if not (health and health.get("service") == "chaser-agent"):
        return True, "Chaser isn't running."
    pid_file = Path(settings["data_dir"]) / PID_FILE
    pid = None
    try:
        pid = int(pid_file.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        pass
    listening = _listening_pid(port)
    if listening is not None and listening != pid:
        pid = listening  # started some other way, such as Start-ChaserAgent.ps1
    if pid is None:
        return False, f"Couldn't find Chaser's process on port {port}."
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        return False, f"Couldn't stop Chaser: {exc}"
    for _ in range(40):
        if not setup_checks.gateway_health(port, timeout=0.5):
            pid_file.unlink(missing_ok=True)
            return True, "Chaser stopped. Its work and receipts are kept."
        time.sleep(0.25)
    return False, "Chaser is still answering. Try again."


# --- Talking to the running service ------------------------------------------

def _service_call(settings: dict[str, Any], method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
    from chaser_agent import agent_cli

    args = argparse.Namespace(data_dir=str(settings["data_dir"]), port=int(settings["port"]))
    return agent_cli._call(args, method, path, body)


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


def add_key(settings: dict[str, Any]) -> bool:
    print(paint("  Get a key from your ChaseOS account page. It won't show as you paste it.", "dim"))
    try:
        key = getpass.getpass("  ChaseOS Cloud key: ")
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
        if status == 200:
            check = reply.get("check") or {}
            credits = f", {check['credits']:,.0f} credits left" if check.get("credits") is not None else ""
            print(f"  {paint('✓', 'ok')} Saved for this Windows account only, and Chaser is using it now{credits}.")
            return True
        message = (reply.get("error") or {}).get("message") if isinstance(reply, dict) else None
        print(f"  {paint('✗', 'fail')} {message or 'Chaser could not save the key.'}")
        return False
    print("  Checking it with ChaseOS Cloud…")
    result = cloud_key.check(key)
    if result.get("refused"):
        print(f"  {paint('✗', 'fail')} {result['reason']}")
        return False
    try:
        cloud_key.save(key)
    except cloud_key.KeyStoreUnavailable as exc:
        print(f"  {paint('✗', 'fail')} {exc}")
        return False
    if result["ok"]:
        credits = f", {result['credits']:,.0f} credits left" if result.get("credits") is not None else ""
        print(f"  {paint('✓', 'ok')} Accepted{credits}. Saved for this Windows account only.")
    else:
        print(f"  {paint('!', 'warn')} Saved. {result['reason']} Chaser will try it when it needs it.")
    return True


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
    print(paint("\nChaser Agent · setup", "head"))
    print("Chaser works on this computer. It keeps a receipt for every step and asks you\n"
          "before anything leaves it. This takes a couple of minutes; change any of it later\n"
          "with " + paint("chaser setup", "teal") + ".")
    advanced = False
    if interactive:
        print("\n  QuickStart  sensible defaults: asks only for your key and your name\n  Advanced    also choose the folder, port and packs")
        advanced = ask("QuickStart or Advanced? [Q/a]").lower().startswith("a")

    heading(f"Step 1 of {total} · Checking this computer")
    show_rows(setup_checks.run(settings)["rows"])

    heading(f"Step 2 of {total} · Where Chaser keeps its work")
    if interactive and advanced:
        folder = ask("Folder", settings["data_dir"])
        port = ask("Port", str(settings["port"]))
        packs = ask("Packs to load, separated by ;", ";".join(settings.get("packs") or []))
        settings = chaser_home.save({"data_dir": folder, "port": int(port) if port.isdecimal() else settings["port"],
                                     "packs": [p.strip() for p in packs.split(";") if p.strip()]})
    for line in setup_checks.fix(settings) or [f"{settings['data_dir']} is ready"]:
        print(f"  {paint('✓', 'ok')} {line}")

    heading(f"Step 3 of {total} · How Chaser thinks")
    print(paint("  ChaseOS Cloud runs Chaser's unattended work, metered in credits on your own key.\n"
                "  Claude Code, if it's installed and signed in, is used next.", "dim"))
    if interactive:
        step_key(settings)
    else:
        print(f"  {MARK['info']} Key: {cloud_key.describe()['source']}. Add one with: chaser key add")

    heading(f"Step 4 of {total} · Your name on approvals")
    if interactive:
        settings = step_name(settings)
    else:
        print(f"  {MARK['info']} {settings.get('reviewer') or 'Not set'}")

    heading(f"Step 5 of {total} · Keys that stop Chaser")
    show_shortcuts(settings)

    heading(f"Step 6 of {total} · Start Chaser")
    started = False
    if not args.no_start and (not interactive or confirm("Start Chaser now and open the HUD?")):
        started = step_start(settings, open_hud=interactive)
    else:
        print(f"  {MARK['info']} Not started. Start it any time: chaser gateway")
    from datetime import UTC, datetime

    settings = chaser_home.save({"onboarded_at": datetime.now(UTC).isoformat(timespec="seconds")})
    heading("Done. Try:")
    print(f"  {paint('chaser ask', 'teal')} \"What's waiting on me today?\"\n"
          f"  {paint('chaser open', 'teal')}      the HUD{'' if started else ' (start Chaser first: chaser gateway)'}\n"
          f"  {paint('chaser setup', 'teal')}     change any of this\n"
          f"  {paint('chaser doctor', 'teal')}    check everything again")
    return 0


def run_gateway(args: argparse.Namespace) -> int:
    settings = chaser_home.load()
    action = args.action
    if action == "start" and args.foreground:
        from chaser_agent import cli

        return cli.main(gateway_command(settings)[5:])
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
        return 0
    if action == "logs":
        log = Path(settings["data_dir"]) / "service.log"
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
    report = setup_checks.run(settings, online=args.online)
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
    if args.action == "check" and found["source"] != "none":
        result = cloud_key.check(os.environ.get("CHASEOS_CLOUD_KEY") or cloud_key.load())
        credits = f", {result['credits']:,.0f} credits left" if result.get("credits") is not None else ""
        print(f"{MARK['ok']} ChaseOS Cloud accepts it{credits}." if result["ok"] else f"{MARK['fail']} {result['reason']}")
        return 0 if result["ok"] else 1
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
            heading("Chaser setup" + paint(f"   {'running' if running else 'not running'} on 127.0.0.1:{settings['port']}", "ok" if running else "dim"))
            key_text = {"environment": "from your vault", "saved": "saved", "none": "not added"}[found["source"]]
            stop = shortcuts.label(settings["shortcuts"]["stop"]) if settings["shortcuts"].get("stop") else "not set"
            for number, title, value in (("1", "ChaseOS Cloud key", key_text), ("2", "Where Chaser keeps its work", settings["data_dir"]),
                                         ("3", "Your name on approvals", settings.get("reviewer") or "not set"),
                                         ("4", "Packs", str(len(settings.get("packs") or [])) or "none"), ("5", "Shortcuts", f"Stop {stop}"),
                                         ("6", "Run the checks", ""), ("7", "Stop Chaser" if running else "Start Chaser", "")):
                print(f"  {paint(number, 'teal')}  {title:<30} {paint(value, 'dim')}")
            print(f"  {paint('q', 'teal')}  Done")
            choice = ask("Choose").lower()
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
            show_rows(setup_checks.run(settings, online=True)["rows"])
        elif choice == "7":
            if _running(settings):
                print("  " + gateway_stop(settings)[1])
            else:
                step_start(settings)
        if args.section:
            return 0
        choice = ""


def run_home(_: argparse.Namespace) -> int:
    settings = chaser_home.load()
    if not settings.get("onboarded_at"):
        print("Chaser isn't set up on this computer yet.")
        if interactive_terminal() and confirm("Set it up now?"):
            return run_onboard(argparse.Namespace(reset=False, data_dir=None, port=None, reviewer=None, pack=[], non_interactive=False, no_start=False))
        print("Run: chaser onboard")
        return 0
    report = setup_checks.run(settings)
    heading("Chaser Agent")
    show_rows([item for item in report["rows"] if item["id"] in {"gateway", "routes", "cloud_key", "reviewer"}])
    print("\n  " + "   ".join(paint(c, "teal") for c in ("chaser ask \"…\"", "chaser open", "chaser gateway", "chaser setup", "chaser doctor")))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chaser", description="Set up, start and check Chaser Agent.",
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
    onboard.set_defaults(func=run_onboard)
    gateway = sub.add_parser("gateway", help="Start, stop or check Chaser's service.")
    gateway.add_argument("action", nargs="?", default="start", choices=["start", "stop", "restart", "status", "logs"])
    gateway.add_argument("--foreground", action="store_true", help="Run in this terminal instead of the background.")
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
    key.add_argument("action", nargs="?", default="status", choices=["status", "add", "check", "remove"])
    key.set_defaults(func=run_key)
    keys = sub.add_parser("shortcuts", help="The keys that stop Chaser or take over.")
    keys.add_argument("action", nargs="?", default="show", choices=["show", "set", "reset"])
    keys.add_argument("name", nargs="?", choices=list(shortcuts.NAMES))
    keys.add_argument("chord", nargs="?", help="For example Ctrl+Alt+Shift+X")
    keys.set_defaults(func=run_shortcuts)
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
