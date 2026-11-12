"""Keeping Chaser running: a supervisor that restarts the service if it stops, and an optional start at sign-in.

    chaser gateway            starts the supervisor in the background, which starts the service
    chaser gateway run        the supervisor in this terminal (what sign-in and `start` run)
    chaser gateway install    start Chaser whenever you sign in to Windows (per user, no admin)
    chaser gateway uninstall  stop doing that

The supervisor restarts the service after a crash, waiting longer each time (2 s up to a minute), and
starts over once the service has stayed up for two minutes. A stop request is a file in the data
folder, so stopping is clean and never races a restart. Nothing here runs a scheduled job or a task:
the service only answers requests from the HUD, the terminal and the packs it was started with.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from chaser_agent import setup_checks

SUPERVISOR_PID = "gateway.pid"
SERVICE_PID = "service.pid"
STOP_FILE = "gateway.stop"
BACKOFF = (2, 5, 15, 30, 60)
HEALTHY_AFTER = 120  # seconds up before a crash counts as new, not part of a loop
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "Chaser Agent"
FLAGS = (getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)) if os.name == "nt" else 0
BREAKAWAY = getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000) if os.name == "nt" else 0


def source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def service_command(settings: dict[str, Any]) -> list[str]:
    command = [sys.executable, "-X", "utf8", "-m", "chaser_agent.cli", "serve", "--data-dir", str(settings["data_dir"]),
               "--port", str(settings["port"]), "--memory-limit-mb", str(settings.get("memory_limit_mb") or 0)]
    for pack in settings.get("packs") or []:
        command += ["--pack", str(pack)]
    return command


def _env() -> dict[str, str]:
    path = os.pathsep.join(p for p in (str(source_root()), os.environ.get("PYTHONPATH", "")) if p)
    return {**os.environ, "PYTHONUTF8": "1", "PYTHONPATH": path}


def _note(log: Path, text: str) -> None:
    with open(log, "a", encoding="utf-8") as stream:
        stream.write(f"{datetime.now(UTC).isoformat(timespec='seconds')} supervisor: {text}\n")


def supervise(settings: dict[str, Any], *, max_restarts: int | None = None, sleep: Callable[[float], None] = time.sleep,
              command: list[str] | None = None, healthy_after: float = HEALTHY_AFTER) -> int:
    """Run the service and restart it when it stops, until asked to stop. Returns how many times it restarted."""
    folder = Path(settings["data_dir"])
    if not folder.exists():
        setup_checks.make_private_folder(folder)
    log, stop = folder / "service.log", folder / STOP_FILE
    stop.unlink(missing_ok=True)
    (folder / SUPERVISOR_PID).write_text(str(os.getpid()), encoding="ascii")
    if command is None:  # the real service, not a test's stand-in: serve any messaging channels beside it
        from chaser_agent import channels

        channels.start_background(settings, lambda line: _note(log, line))
    restarts, failures = 0, 0
    try:
        while True:
            started = time.monotonic()
            with open(log, "ab") as out, open(str(log) + ".err", "ab") as err:
                child = subprocess.Popen(command or service_command(settings), cwd=str(folder), env=_env(),
                                         stdin=subprocess.DEVNULL, stdout=out, stderr=err)
            (folder / SERVICE_PID).write_text(str(child.pid), encoding="ascii")
            while child.poll() is None:
                if stop.exists():
                    child.terminate()
                    child.wait(30)
                    break
                sleep(0.5)
            if stop.exists():
                _note(log, "stopped on request")
                return restarts
            failures = 1 if time.monotonic() - started >= healthy_after else failures + 1
            wait = BACKOFF[min(failures - 1, len(BACKOFF) - 1)]
            _note(log, f"the service stopped (code {child.returncode}); starting it again in {wait} s")
            if max_restarts is not None and restarts >= max_restarts:
                return restarts
            restarts += 1
            sleep(wait)
    finally:
        for name in (SUPERVISOR_PID, SERVICE_PID, STOP_FILE):
            (folder / name).unlink(missing_ok=True)


def start_detached(settings: dict[str, Any], *, wait: float = 60) -> tuple[bool, str]:
    """Start the supervisor in the background and wait until the service answers."""
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
    command = [sys.executable, "-X", "utf8", "-m", "chaser_agent", "gateway", "run"]
    with open(str(log) + ".supervisor", "ab") as out:
        try:
            # Out of the terminal's job too, so closing the terminal that started it doesn't end Chaser.
            process = subprocess.Popen(command, cwd=str(folder), env=_env(), stdin=subprocess.DEVNULL, stdout=out, stderr=out,
                                       creationflags=FLAGS | BREAKAWAY, start_new_session=os.name != "nt", close_fds=True)
        except OSError:
            process = subprocess.Popen(command, cwd=str(folder), env=_env(), stdin=subprocess.DEVNULL, stdout=out, stderr=out,
                                       creationflags=FLAGS, start_new_session=os.name != "nt", close_fds=True)
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False, f"Chaser stopped as it started. See {log}.err"
        health = setup_checks.gateway_health(port, timeout=1)
        if health and health.get("service") == "chaser-agent":
            return True, f"Chaser is running on http://127.0.0.1:{port}/, and comes back by itself if it stops"
        time.sleep(0.5)
    return False, f"Chaser didn't answer within {int(wait)} seconds. See {log}.err"


def _listening_pid(port: int) -> int | None:
    if os.name != "nt":
        return None
    done = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, timeout=20)
    for line in done.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[1] == f"127.0.0.1:{port}" and parts[3].upper() == "LISTENING":
            return int(parts[4])
    return None


def _kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=30)
    else:
        import signal

        os.kill(pid, signal.SIGTERM)


def stop(settings: dict[str, Any]) -> tuple[bool, str]:
    port = int(settings["port"])
    health = setup_checks.gateway_health(port)
    if not (health and health.get("service") == "chaser-agent"):
        return True, "Chaser isn't running."
    folder = Path(settings["data_dir"])
    (folder / STOP_FILE).write_text("stop", encoding="ascii")  # the supervisor stops the service and exits
    for _ in range(40):
        if not setup_checks.gateway_health(port, timeout=0.5):
            return True, "Chaser stopped. Its work and receipts are kept."
        time.sleep(0.25)
    # No supervisor answered (started by Start-ChaserAgent.ps1 or an older version): stop the process itself.
    pid = _listening_pid(port)
    (folder / STOP_FILE).unlink(missing_ok=True)
    if pid is None:
        return False, f"Couldn't find Chaser's process on port {port}."
    _kill_tree(pid)
    for _ in range(40):
        if not setup_checks.gateway_health(port, timeout=0.5):
            return True, "Chaser stopped. Its work and receipts are kept."
        time.sleep(0.25)
    return False, "Chaser is still answering. Try again."


# --- Starting at sign-in ----------------------------------------------------------------------

def sign_in_command() -> str:
    """What Windows runs at sign-in: the supervisor, with no console window."""
    windowless = Path(sys.executable).with_name("pythonw.exe")
    python = windowless if windowless.is_file() else Path(sys.executable)
    return f'"{python}" -X utf8 -m chaser_agent gateway run'


def installed() -> str | None:
    """The sign-in command if Chaser starts at sign-in, else None."""
    if os.name != "nt":
        return None
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            return str(winreg.QueryValueEx(key, RUN_VALUE)[0])
    except OSError:
        return None


def install() -> str:
    if os.name != "nt":
        raise OSError("Starting at sign-in is only set up on Windows so far. Run `chaser gateway run` from your own service manager.")
    import winreg

    command = sign_in_command()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, command)
    return command


def uninstall() -> bool:
    if os.name != "nt" or installed() is None:
        return False
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.DeleteValue(key, RUN_VALUE)
    return True


def follow(paths: list[Path], *, lines: int = 40, poll: float = 0.5, out=sys.stdout) -> None:
    """Print the last lines of each log, then new lines as they're written, until Ctrl+C."""
    positions: dict[Path, int] = {}
    for path in paths:
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace").splitlines()
            out.write("\n".join(text[-lines:]) + ("\n" if text else ""))
            positions[path] = path.stat().st_size
    out.flush()
    while True:
        time.sleep(poll)
        for path in paths:
            if not path.is_file():
                continue
            size = path.stat().st_size
            start = positions.get(path, 0)
            if size < start:
                start = 0  # the log was replaced
            if size > start:
                with open(path, "rb") as stream:
                    stream.seek(start)
                    out.write(stream.read().decode("utf-8", errors="replace").replace("\r\n", "\n"))
                out.flush()
            positions[path] = size
