"""Drive the HUD in a hidden Edge against a scripted agent, and check what a person would see.

    python scripts/check_hud.py --out <folder>

It starts its own service on a temporary folder and port with scripts/hud_check_pack.py, so it
needs no model and touches no real data. No window appears. Each state is a separate check,
and screenshots of the main ones go in the folder. A run that needs a real desktop window, such
as staying on top or minimizing, isn't covered here. Windows with Edge only.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from chaser_agent.local_acl import read_private_control_token

ROOT = Path(__file__).resolve().parents[1]
EDGE = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
PACK = ROOT / "scripts" / "hud_check_pack.py"
LONG_NAME = "/Chaser Agent/.test(document.body.innerText)"  # on screen it's Chaser; Chaser Agent is the product name
TAGS = "[...document.querySelectorAll('.row .tag')].map(n => n.textContent)"


class Page:
    """Just enough of the DevTools protocol, with the standard library."""

    def __init__(self, debug_port: int, match: str) -> None:
        deadline = time.monotonic() + 30
        target = None
        while time.monotonic() < deadline and target is None:
            try:
                rows = json.load(urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json", timeout=3))
                target = next((row for row in rows if row["type"] == "page" and match in row["url"]), None)
            except OSError:
                pass
            time.sleep(0.3)
        if target is None:
            raise SystemExit("The hidden browser did not open the HUD")
        address = target["webSocketDebuggerUrl"].split("/", 3)
        host, port = address[2].split(":")
        self.socket = socket.create_connection((host, int(port)), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.socket.sendall(f"GET /{address[3]} HTTP/1.1\r\nHost: {address[2]}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode())
        buffer = b""
        while b"\r\n\r\n" not in buffer:
            buffer += self.socket.recv(4096)
        self.next_id = 0

    def _exact(self, count: int) -> bytes:
        out = b""
        while len(out) < count:
            out += self.socket.recv(count - len(out))
        return out

    def call(self, method: str, **params: object) -> dict:
        self.next_id += 1
        data = json.dumps({"id": self.next_id, "method": method, "params": params}).encode()
        mask = os.urandom(4)
        size = len(data)
        head = bytes([0x81]) + (bytes([0x80 | size]) if size < 126 else bytes([0x80 | 126]) + struct.pack(">H", size) if size < 65536 else bytes([0x80 | 127]) + struct.pack(">Q", size))
        self.socket.sendall(head + mask + bytes(byte ^ mask[index % 4] for index, byte in enumerate(data)))
        while True:
            parts = b""
            while True:
                first, second = self._exact(2)
                length = second & 127
                if length == 126:
                    length = struct.unpack(">H", self._exact(2))[0]
                elif length == 127:
                    length = struct.unpack(">Q", self._exact(8))[0]
                parts += self._exact(length)
                if first & 0x80:
                    break
            message = json.loads(parts.decode())
            if message.get("id") == self.next_id:
                return message.get("result", message)

    def js(self, expression: str) -> object:
        result = self.call("Runtime.evaluate", expression=expression, awaitPromise=True, returnByValue=True)
        return result.get("result", {}).get("value")

    def until(self, expression: str, seconds: float = 20.0) -> bool:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self.js(expression):
                return True
            time.sleep(0.2)
        return False

    def shot(self, path: Path) -> None:
        path.write_bytes(base64.b64decode(self.call("Page.captureScreenshot", format="png")["data"]))


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _serve(data: Path, port: int, *, no_model: bool = False) -> subprocess.Popen:
    # Its own settings folder and no Cloud key, so the check never reads this computer's real ones or calls ChaseOS Cloud.
    env = {key: value for key, value in os.environ.items() if key != "CHASEOS_CLOUD_KEY"}
    env.update({"HUD_CHECK_NO_MODEL": "1" if no_model else "", "CHASER_AGENT_HOME": str(data.parent / "home"), "CHASEOS_CLOUD_BASE_URL": "http://127.0.0.1:9"})
    process = subprocess.Popen(
        [sys.executable, "-B", "-X", "utf8", "-m", "chaser_agent.cli", "serve", "--data-dir", str(data), "--port", str(port), "--pack", str(PACK), "--memory-limit-mb", "800"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return process
        except OSError:
            time.sleep(0.3)
    process.terminate()
    raise SystemExit("The service did not start")


class Checks:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def __call__(self, name: str, passed: object, detail: object = None) -> bool:
        self.rows.append({"check": name, "passed": bool(passed), **({"detail": detail} if detail is not None and not passed else {})})
        return bool(passed)


def main_phase(page: Page, check: Checks, out: Path) -> None:
    def text(element_id: str) -> str:
        return str(page.js(f"document.getElementById('{element_id}').textContent"))

    def click(selector: str) -> None:
        page.js(f"document.querySelector({json.dumps(selector)}).click()")

    def click_text(selector: str, wording: str) -> None:
        page.js(f"[...document.querySelectorAll({json.dumps(selector)})].find(n => n.textContent.includes({json.dumps(wording)})).click()")

    def send(message: str) -> None:
        page.js(f"(() => {{ const box = document.getElementById('input'); box.value = {json.dumps(message)}; box.dispatchEvent(new KeyboardEvent('keydown', {{key: 'Enter', bubbles: true}})); }})()")

    opened = "document.getElementById('hud').classList.contains('open')"

    # Idle pill.
    check("starts ready", page.until("document.getElementById('state-text').textContent === 'Ready'"), text("state-text"))
    check("starts collapsed at pill height", page.until(f"!{opened} && innerHeight <= 80 && innerWidth === 420"), page.js("[innerWidth, innerHeight]"))
    check("panel is hidden when collapsed", page.js("document.getElementById('panel').hidden"))
    check("no sideways overflow in the pill", page.js("document.documentElement.scrollWidth <= innerWidth"))
    check("Stop isn't offered with nothing running", page.js("document.getElementById('stop').hidden"))
    page.shot(out / "01-pill-idle.png")

    # Open, examples, parent link, Esc.
    click("#chevron")
    check("opening grows the window", page.until(f"{opened} && innerHeight > 400"), page.js("innerHeight"))
    check("examples are offered", page.until("document.querySelectorAll('.suggestion').length >= 1"))
    click(".suggestion")
    check("an example fills the input", page.js("document.getElementById('input').value.startsWith('An example')"))
    page.js("document.getElementById('input').value = ''")
    check("the parent link shows", page.until("!document.getElementById('parent').hidden && document.getElementById('parent').textContent === 'Open Parent'"))
    check("on screen it is Chaser, never Chaser Agent", not page.js(LONG_NAME))
    check("a first run offers setup", page.until("!document.getElementById('welcome').hidden"))
    page.shot(out / "02-panel-idle.png")
    settings_phase(page, check, out)
    page.js("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}))")
    check("Esc closes the panel", page.until(f"!{opened} && innerHeight <= 80"))

    # A run that reaches a question while collapsed.
    send("SCRIPT:main please do the whole thing")
    check("a sentence and Enter starts work", page.until("document.getElementById('input').value === '' && !document.getElementById('goal').hidden"))
    check("the panel opens itself for a question", page.until(f"{opened} && document.querySelector('#pending h3')?.textContent === 'Chaser needs something from you'"))
    check("the question stays on the pill", "Which colour" in text("now"), text("now"))
    check("the taskbar title says a person is needed", page.until("document.title === 'Needs your answer · Chaser'"), page.js("document.title"))
    check("amber while waiting for a person", page.js("document.getElementById('hud').dataset.tone === 'human'"))
    check("Stop is offered while waiting", not page.js("document.getElementById('stop').hidden"))
    tags = page.js(TAGS)
    check("reads, failures and refusals each have their tag", all(tag in (tags or []) for tag in ("READ", "FAILED", "REFUSED")), tags)
    check("the plan isn't shown as an action", not page.js("[...document.querySelectorAll('.row')].some(r => r.textContent.includes('Updated the plan'))"))
    check("a hostile argument stays as text", page.js("!document.querySelector('.activity img') && window.__pwned === undefined && document.querySelector('.row em').textContent.includes('onerror')"), page.js("document.querySelector('.row em')?.textContent"))
    check("the first message isn't repeated in the list", page.js("document.querySelectorAll('.said').length === 0"))
    check("refusals and failures come first in the counts", text("meta").startswith("1 refused · 1 failed · "), text("meta"))
    page.shot(out / "03-question.png")

    # Inspect a row.
    click(".row")
    check("a row opens to show why, what it asked and what came back", page.until("(() => { const box = document.querySelector('.inspect'); return box && box.textContent.includes('Why') && box.textContent.includes('Reading first.') && box.textContent.includes('What it asked for') && box.textContent.includes('demo read result'); })()"), page.js("document.querySelector('.inspect')?.textContent"))
    page.shot(out / "04-inspect.png")
    click(".row")
    check("clicking again closes it", page.until("!document.querySelector('.inspect')"))

    # Answer with a button, then both approval answers.
    click_text(".pending .control", "Blue")
    check("the answer shows in the list", page.until("[...document.querySelectorAll('.said')].some(n => n.textContent === 'Blue')"))
    check("the approval asks about the exact action", page.until("document.querySelector('#pending h3')?.textContent === 'Say yes to this exact action?' && document.querySelector('#pending strong')?.textContent === 'First gated action'"), page.js("document.getElementById('pending').textContent"))
    check("the exact request can be read", page.js("document.querySelector('#pending details pre').textContent.includes('The exact words of the first request.')"))
    check("the plan line shows the active step", page.until("document.getElementById('progress').textContent.includes('Step 2 of 3')"), text("progress"))
    tags = page.js(TAGS)
    check("saves and drafts have their tags", "SAVED" in (tags or []) and "DRAFT" in (tags or []), tags)
    page.shot(out / "05-approval.png")
    click_text(".pending .control", "No")
    check("No is recorded", page.until("[...document.querySelectorAll('.tag')].some(n => n.textContent === 'YOU: NO')"))
    check("the next approval replaces the first", page.until("document.querySelector('#pending strong')?.textContent === 'Second gated action'"), page.js("document.getElementById('pending').textContent"))
    check("the buttons stay in view on a long request", page.js("(() => { const yes = document.querySelector('.pending .yes').getBoundingClientRect(); const input = document.querySelector('.composer').getBoundingClientRect(); return yes.top > 0 && yes.bottom <= input.top; })()"), page.js("JSON.stringify(document.querySelector('.pending .yes').getBoundingClientRect())"))
    check("a long request doesn't push the list away", page.js("document.getElementById('activity').clientHeight >= 60"), page.js("document.getElementById('activity').clientHeight"))
    page.shot(out / "05b-long-approval.png")
    click_text(".pending .yes", "Yes")
    check("Yes is recorded", page.until("[...document.querySelectorAll('.tag')].some(n => n.textContent === 'YOU: YES')"))

    # Finished.
    check("it finishes", page.until("document.getElementById('state-text').textContent === 'Finished'"), text("state-text"))
    tags = page.js(TAGS)
    check("no action is listed twice", (tags or []).count("REFUSED") == 1 and (tags or []).count("FAILED") == 1 and (tags or []).count("DRAFT") == 1, tags)
    check("the injection warning shows", page.js("[...document.querySelectorAll('.flag')].some(n => n.textContent.includes('tried to give instructions'))"))
    check("the answer shows", page.js("document.querySelector('.answer')?.textContent === 'All finished. Nothing was sent.'"))
    check("the answer is on the pill", "All finished" in text("now"), text("now"))
    check("teal when finished", page.js("document.getElementById('hud').dataset.tone === 'done'"))
    check("Stop goes away when finished", page.js("document.getElementById('stop').hidden"))
    check("the taskbar title goes back", page.js("document.title === 'Chaser'"))
    check("a finished session doesn't show a stale step", page.js("document.getElementById('progress').hidden"))
    first = text("meta")
    time.sleep(2.5)
    check("the clock stops when finished", text("meta") == first, [first, text("meta")])
    check("still Chaser, never Chaser Agent, when finished", not page.js(LONG_NAME))
    page.shot(out / "06-finished.png")

    # A saved page opens sandboxed and the window goes back afterwards.
    check("files are offered", page.until("!document.getElementById('files-button').hidden"))
    click("#files-button")
    check("the file is listed", page.until("!document.getElementById('drawer').hidden && document.getElementById('drawer').textContent.includes('report.html')"))
    before = page.js("innerHeight")
    click_text(".pick", "report.html")
    check("the file opens in a sandbox", page.until("document.getElementById('viewer').open && document.getElementById('viewer-frame').getAttribute('sandbox') === '' && !document.getElementById('viewer-frame').hidden"))
    check("the window grows to read it", page.until("innerWidth > 800"), page.js("innerWidth"))
    time.sleep(0.5)
    check("a script in the page can't run", page.js("window.__pwned === undefined"))
    page.shot(out / "07-file.png")
    click("#viewer-close")
    check("the window goes back after reading", page.until(f"innerWidth === 420 && innerHeight === {before}"), page.js("[innerWidth, innerHeight]"))

    # A follow-up on the same session, after long enough that the clock would show it.
    time.sleep(11)
    send("SCRIPT:main one more thing please")
    check("a follow-up shows as a message", page.until("[...document.querySelectorAll('.said')].some(n => n.textContent.startsWith('SCRIPT:main one more'))"))
    check("the follow-up is answered", page.until("[...document.querySelectorAll('.answer')].some(n => n.textContent.startsWith('Second answer'))"))
    check("the first message returns to the list once there's a second", page.js("document.querySelector('.said').textContent.startsWith('SCRIPT:main please') && document.querySelectorAll('.said')[0] === document.getElementById('activity').firstElementChild"), page.js("[...document.querySelectorAll('.said')].map(n => n.textContent)"))
    check("the clock restarts for a follow-up", page.js("/^(.*· )?0:0\\d$/.test(document.getElementById('meta').textContent)"), text("meta"))
    check("the goal line shows the latest message", page.js("document.getElementById('goal').textContent.startsWith('SCRIPT:main one more')"), page.js("document.getElementById('goal').textContent"))

    # New, then Stop.
    click("#new-work")
    check("New goes back to ready", page.until("document.getElementById('state-text').textContent === 'Ready' && document.getElementById('goal').hidden && !!document.getElementById('empty')"), text("state-text"))
    send("SCRIPT:slow take your time")
    check("a running tool shows as running", page.until("[...document.querySelectorAll('.row .tag')].some(n => n.textContent === 'RUNNING')"), page.js(TAGS))
    check("blue while working", page.until("document.getElementById('hud').dataset.tone === 'live'"))
    click("#stop")
    check("Stop stops it", page.until("document.getElementById('state-text').textContent === 'Cancelled'"), text("state-text"))
    check("Stop goes away afterwards", page.until("document.getElementById('stop').hidden"))

    # Earlier work.
    click("#recent-button")
    check("earlier work is listed", page.until("!document.getElementById('drawer').hidden && document.querySelectorAll('#drawer .pick').length >= 2"), page.js("document.getElementById('drawer').textContent"))
    click_text(".pick", "SCRIPT:main")
    check("an old session comes back in full", page.until("document.querySelectorAll('.row').length >= 8 && !!document.querySelector('.answer')"), page.js(TAGS))
    tags = page.js(TAGS)
    check("reopening doesn't duplicate rows", (tags or []).count("REFUSED") == 1, tags)
    check("the drawer closes after choosing", page.js("document.getElementById('drawer').hidden"))

    # A reload while something is waiting, then a typed answer.
    click("#new-work")
    send("SCRIPT:ask a question please")
    check("a free-text question shows", page.until("document.querySelector('#pending h3')?.textContent === 'Chaser needs something from you' && document.querySelector('#pending p').textContent.includes('called')"))
    page.js("location.reload()")
    time.sleep(1)
    check("a waiting question comes back after a reload", page.until("document.querySelector('#pending p')?.textContent.includes('called')", 15), page.js("document.getElementById('pending')?.textContent"))
    page.js("(() => { const box = document.querySelector('#pending textarea'); box.value = 'Quarterly'; document.querySelector('#pending .yes').click(); })()")
    check("a typed answer goes through", page.until("document.querySelector('.answer')?.textContent === 'Called what you said.'"), page.js("document.getElementById('activity').textContent"))
    check("no script error from anything above", page.js("window.__pwned === undefined"))


def settings_phase(page: Page, check: Checks, out: Path) -> None:
    """The first-run walk-through: Cloud key, your name, shortcuts, checks. The key is fake and never leaves the computer."""
    def body(text: str) -> str:
        return f"document.getElementById('settings-body').textContent.includes({json.dumps(text)})"

    def next_step() -> None:
        page.js("document.querySelector('#settings-foot .yes').click()")

    page.js("document.getElementById('welcome-start').click()")
    check("setup opens on the Cloud key step", page.until(f"!document.getElementById('settings').hidden && {body('Not added yet.')}"), page.js("document.getElementById('settings-body').textContent"))
    check("setup says which step this is", page.js("document.getElementById('settings-foot').textContent.includes('Step 1 of 4')"))
    check("the key field hides what is typed", page.js("document.querySelector('#settings-body input').type === 'password'"))
    check("no sideways overflow in settings", page.js("document.documentElement.scrollWidth <= innerWidth"))
    page.shot(out / "10-setup-key.png")
    page.js("(() => { const box = document.querySelector('#settings-body input'); box.value = 'hud-check-not-a-real-key'; document.querySelector('#settings-body form').requestSubmit(); })()")
    check("a key is saved and the field is cleared", page.until(f"{body('Saved.')} && document.querySelector('#settings-body input').value === ''"), page.js("document.getElementById('settings-body').textContent"))
    check("the key is never shown again", not page.js("document.body.innerText.includes('hud-check-not-a-real-key')"))
    check("an unreachable Cloud is said plainly", page.js(body("Couldn't reach ChaseOS Cloud")))
    page.shot(out / "11-setup-key-saved.png")
    page.js("document.querySelector('#settings-body .danger').click()")
    check("removing asks twice", page.until(body("Click again to remove")))
    page.js("document.querySelector('#settings-body .danger').click()")
    check("the key can be removed", page.until(f"{body('Not added yet.')} && !document.querySelector('#settings-body .danger')"))
    next_step()
    check("step 2 asks for your name", page.until(body("Your name on approvals")))
    page.js("(() => { document.querySelector('#settings-body input').value = 'HUD Check'; document.querySelector('#settings-body form').requestSubmit(); })()")
    check("the name is saved", page.until(body('signed "HUD Check (HUD)"')), page.js("document.getElementById('settings-body').textContent"))
    next_step()
    check("step 3 shows the shortcuts", page.until("document.querySelectorAll('.key-row').length === 3 && document.querySelector('.key-row kbd').textContent === 'Ctrl'"))
    check("each shortcut says whether it is free", page.js("[...document.querySelectorAll('.key-row .dot')].every(n => /Free|Taken|checked/.test(n.textContent))"), page.js("[...document.querySelectorAll('.key-row .dot')].map(n => n.textContent)"))
    page.shot(out / "12-setup-shortcuts.png")
    page.js("document.querySelectorAll('.key-row .caps')[2].click()")
    check("clicking the keys listens for new ones", page.until("!!document.querySelector('.caps.listening')"))
    page.js("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'E', code: 'KeyE', ctrlKey: true, altKey: true, bubbles: true}))")
    check("a chord the keyboard uses for characters is refused", page.until("document.querySelector('#settings-body .result.fail')?.textContent.includes('AltGr')"), page.js("document.querySelector('#settings-body .result')?.textContent"))
    page.js("document.querySelectorAll('.key-row .caps')[2].click()")
    page.js("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Y', code: 'KeyY', ctrlKey: true, altKey: true, shiftKey: true, bubbles: true}))")
    check("a free chord is taken", page.until("[...document.querySelectorAll('.key-row')][2].textContent.includes('Y')"), page.js("[...document.querySelectorAll('.key-row')].map(n => n.textContent)"))
    page.js("[...document.querySelectorAll('#settings-body .link')].find(n => n.textContent.includes('standard')).click()")
    check("the standard keys come back", page.until("[...document.querySelectorAll('.key-row')][2].textContent.includes('T')"))
    next_step()
    check("step 4 runs the checks", page.until("document.querySelectorAll('.check').length >= 6", 30), page.js("document.getElementById('settings-body').textContent"))
    check("the checks show the name and that Chaser is running", page.js("document.querySelector('.check.ok') && " + body("HUD Check") + " && " + body("Running, ready for work")))
    page.shot(out / "13-setup-checks.png")
    next_step()
    check("finishing closes setup and hides the welcome", page.until("document.getElementById('settings').hidden && document.getElementById('welcome').hidden"))
    page.js("document.getElementById('settings-button').click()")
    check("Settings opens again from the foot of the panel", page.until("!document.getElementById('settings').hidden && document.getElementById('settings-title').textContent === 'Settings' && document.getElementById('settings-foot').hidden"))
    page.js("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}))")
    check("Esc closes Settings first, not the panel", page.until("document.getElementById('settings').hidden && document.getElementById('hud').classList.contains('open')"))


def lost_contact_phase(page: Page, check: Checks, process: subprocess.Popen, out: Path) -> None:
    process.terminate()
    process.wait(20)
    check("losing the service is said plainly", page.until("document.getElementById('state-text').textContent === 'Lost contact' && document.getElementById('hud').dataset.tone === 'blocked'", 15), page.js("document.getElementById('state-text').textContent"))
    page.shot(out / "08-lost-contact.png")


def no_model_phase(page: Page, check: Checks, out: Path) -> None:
    check("with no model the HUD says so", page.until("!document.getElementById('route').hidden && document.getElementById('route').textContent.includes('no way to think yet')", 30), page.js("document.getElementById('route').textContent"))
    check("the reasons are in its tooltip", page.js("document.getElementById('route').title.includes('Another harness')"), page.js("document.getElementById('route').title"))
    page.js("(() => { const box = document.getElementById('input'); box.value = 'Anything'; box.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true})); })()")
    check("work without a model stops and says why", page.until("document.getElementById('state-text').textContent === 'Stopped' && document.getElementById('now').textContent.includes('No AI model is connected')"), page.js("[document.getElementById('state-text').textContent, document.getElementById('now').textContent]"))
    check("red when stopped", page.js("document.getElementById('hud').dataset.tone === 'blocked'"))
    page.shot(out / "09-no-model.png")
    page.js("document.getElementById('route').click()")
    check("the no-model line opens the Cloud key setting", page.until("!document.getElementById('settings').hidden && document.getElementById('settings-body').textContent.includes('ChaseOS Cloud key')"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="chaser-hud-check-"))
    port, debug = _free_port(), _free_port()
    check = Checks()
    browser = process = page = None
    try:
        process = _serve(work / "data", port)
        token = read_private_control_token(work / "data")
        browser = subprocess.Popen(
            [str(EDGE), "--headless=new", f"--remote-debugging-port={debug}", f"--user-data-dir={work / 'profile'}", "--no-first-run", "--force-device-scale-factor=2", "--screen-info={3840x2400}", "--window-size=442,115", f"--app=http://127.0.0.1:{port}/#token={token}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        page = Page(debug, f"127.0.0.1:{port}")
        page.call("Page.enable")
        main_phase(page, check, args.out)
        lost_contact_phase(page, check, process, args.out)
        process = _serve(work / "data-no-model", port, no_model=True)
        fresh_token = read_private_control_token(work / "data-no-model")
        page.js(f"sessionStorage.removeItem('chaser-agent-token'); location.href = 'http://127.0.0.1:{port}/#token={fresh_token}'; location.reload(); 'going'")
        time.sleep(2)
        no_model_phase(page, check, args.out)
    finally:
        if page is not None:
            try:
                page.call("Browser.close")
            except OSError:
                pass
        if browser is not None:
            try:
                browser.wait(15)
            except subprocess.TimeoutExpired:
                browser.kill()
        if process is not None:
            process.terminate()
            try:
                process.wait(20)
            except subprocess.TimeoutExpired:
                process.kill()
        shutil.rmtree(work, ignore_errors=True)
    failed = [row for row in check.rows if not row["passed"]]
    result = {"passed": not failed, "checks": len(check.rows), "failed": failed, "rows": check.rows}
    (args.out / "check-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("passed", "checks", "failed")}, ensure_ascii=False, indent=1))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
