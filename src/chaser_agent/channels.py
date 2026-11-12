"""Messaging channels: talk to Chaser from Telegram, Discord, Slack or email, as governed doors rather than open bridges.

- Only allowlisted accounts are heard; everyone else is ignored and noted in the log.
- A message starts or continues a session through the same local API the terminal uses, so every
  approval still stops the work. The approval reaches the person in the same app with the tool, its
  arguments and the first characters of the request's digest; the answer is checked against the
  request that is waiting now and signed "<name> (Telegram)" into the session's hash-chained receipt.
- None needs a public address: Telegram is long-polled; Discord and Slack are read from the bot's direct
  message with each allowed person over their web APIs; email is read over IMAP and answered over SMTP.
  Email counts a sender only when their mail server vouches for them (DKIM or SPF pass), because a From
  line alone can be forged. Tokens and passwords are saved encrypted for this Windows account.
- Photos and image attachments come through as context, saved and hashed into the receipt.

Replies go back only to the account that asked, which is the person's own door; anything a tool
would send anywhere else still needs its own approval.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from chaser_agent import chaser_home, cloud_key

PLATFORMS = {
    "telegram": {"label": "Telegram", "env": "TELEGRAM_BOT_TOKEN", "where": "Message @BotFather, send /newbot, copy the token."},
    "discord": {"label": "Discord", "env": "DISCORD_BOT_TOKEN",
                "where": "discord.com/developers/applications → New Application → Bot → Reset Token. Then invite the bot to a server you're in."},
    "slack": {"label": "Slack", "env": "SLACK_BOT_TOKEN",
              "where": "api.slack.com/apps → Create App → OAuth & Permissions: add bot scopes chat:write, im:history, im:write, files:read; install, copy the xoxb- token."},
    "email": {"label": "Email", "env": "CHASER_EMAIL_PASSWORD",
              "where": "Use an app password from your mail provider (Gmail, Outlook and iCloud all offer them), not your main password."},
}
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_IMAGE = 3 * 1024 * 1024
WAITING = {"awaiting_human", "awaiting_approval"}
DONE = {"finished", "failed", "cancelled", "budget_stopped", "interrupted"}
YES, NO = {"yes", "y", "approve", "ok"}, {"no", "n", "reject"}
LIMIT = 3500  # both platforms cap a message near 4000 characters


# --- Tokens and settings ------------------------------------------------------------

def _token_path(platform: str) -> Path:
    return chaser_home.home() / "keys" / f"channel-{platform}.dpapi"


def save_token(platform: str, token: str) -> None:
    token = cloud_key.validate(token)
    target = _token_path(platform)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".partial")
    temporary.write_text(cloud_key._dpapi(token.encode("utf-16-le"), protect=True).hex(), encoding="ascii")
    os.replace(temporary, target)


def load_token(platform: str, environ: dict[str, str] | None = None) -> str:
    environ = os.environ if environ is None else environ
    if environ.get(PLATFORMS[platform]["env"], "").strip():
        return environ[PLATFORMS[platform]["env"]].strip()
    try:
        raw = _token_path(platform).read_text(encoding="ascii").strip()
        return cloud_key._dpapi(bytes.fromhex(raw), protect=False).decode("utf-16-le") if raw else ""
    except (OSError, ValueError, UnicodeError, cloud_key.KeyStoreUnavailable):
        return ""


def forget_token(platform: str) -> None:
    _token_path(platform).unlink(missing_ok=True)


def configured(settings: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """The channels set up and switched on, with their allowlists."""
    return {name: value for name, value in (settings.get("channels") or {}).items()
            if name in PLATFORMS and value.get("enabled", True) and value.get("allow")}


# --- HTTP ---------------------------------------------------------------------------

def _request(url: str, *, method: str = "GET", body: dict[str, Any] | None = None, headers: dict[str, str] | None = None,
             timeout: float = 35) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:  # noqa: S310 - the platform's own API
            text = reply.read().decode("utf-8")
            return reply.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8") or "{}")
        except ValueError:
            return exc.code, {}
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, ValueError):
        return 0, {}


@dataclass
class Inbound:
    user: str          # the sender's account id: what the allowlist holds
    chat: str          # where to reply
    text: str = ""
    name: str = ""
    button: str = ""   # Telegram button data, for approvals
    button_id: str = ""
    images: list[dict[str, Any]] = field(default_factory=list)  # {name, media_type, data (base64)}


def _image(name: str, media_type: str, raw: bytes) -> dict[str, Any] | None:
    import base64

    if media_type not in IMAGE_TYPES or not raw or len(raw) > MAX_IMAGE:
        return None
    return {"name": name[:60], "media_type": media_type, "data": base64.b64encode(raw).decode("ascii")}


def _download(url: str, headers: dict[str, str] | None = None) -> bytes:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=30) as reply:  # noqa: S310
            return reply.read(MAX_IMAGE + 1)
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
        return b""


class Telegram:
    """The Bot API over long polling: no webhook, no public address."""

    platform, label = "telegram", "Telegram"

    def __init__(self, token: str, request: Callable[..., tuple[int, Any]] = _request) -> None:
        self.base, self.request, self.offset = f"https://api.telegram.org/bot{token}", request, 0

    def whoami(self) -> tuple[bool, str]:
        status, value = self.request(f"{self.base}/getMe", timeout=15)
        ok = status == 200 and value.get("ok")
        return bool(ok), ("@" + value["result"].get("username", "")) if ok else f"Telegram refused the token (HTTP {status or 'no connection'})."

    def poll(self, wait: int = 25) -> list[Inbound]:
        query = urllib.parse.urlencode({"timeout": wait, "offset": self.offset, "allowed_updates": json.dumps(["message", "callback_query"])})
        status, value = self.request(f"{self.base}/getUpdates?{query}", timeout=wait + 10)
        if status != 200 or not value.get("ok"):
            time.sleep(5)
            return []
        out = []
        for update in value.get("result") or []:
            self.offset = max(self.offset, int(update["update_id"]) + 1)
            if "callback_query" in update:
                query = update["callback_query"]
                sender = query.get("from") or {}
                out.append(Inbound(str(sender.get("id")), str((query.get("message") or {}).get("chat", {}).get("id")), name=sender.get("first_name", ""),
                                   button=query.get("data", ""), button_id=query.get("id", "")))
            elif "message" in update and (update["message"].get("text") or update["message"].get("photo")):
                message = update["message"]
                sender = message.get("from") or {}
                images = [i for i in [self._photo(message["photo"][-1])] if i] if message.get("photo") else []
                text = message.get("text") or message.get("caption") or ("What's in this picture?" if images else "")
                out.append(Inbound(str(sender.get("id")), str(message["chat"]["id"]), text, sender.get("first_name", ""), images=images))
        return out

    def _photo(self, photo: dict[str, Any]) -> dict[str, Any] | None:
        status, value = self.request(f"{self.base}/getFile?file_id={urllib.parse.quote(str(photo.get('file_id')))}", timeout=20)
        path = (value.get("result") or {}).get("file_path") if status == 200 else None
        if not path:
            return None
        return _image(Path(path).name, "image/jpeg", _download(self.base.replace("/bot", "/file/bot", 1) + "/" + path))

    def send(self, chat: str, text: str, buttons: list[tuple[str, str]] | None = None) -> None:
        body: dict[str, Any] = {"chat_id": chat, "text": text[:LIMIT]}
        if buttons:
            body["reply_markup"] = {"inline_keyboard": [[{"text": label, "callback_data": data} for label, data in buttons]]}
        self.request(f"{self.base}/sendMessage", method="POST", body=body, timeout=20)

    def acknowledge(self, button_id: str, text: str) -> None:
        if button_id:
            self.request(f"{self.base}/answerCallbackQuery", method="POST", body={"callback_query_id": button_id, "text": text[:180]}, timeout=20)


class Discord:
    """The bot's direct messages with each allowlisted person, read over REST: no gateway connection, no public address."""

    platform, label = "discord", "Discord"
    API = "https://discord.com/api/v10"

    def __init__(self, token: str, allow: list[str], request: Callable[..., tuple[int, Any]] = _request, state: dict[str, Any] | None = None) -> None:
        self.headers = {"Authorization": f"Bot {token}", "User-Agent": "DiscordBot (https://chaseos.ai, 1)"}
        self.request, self.allow = request, allow
        self.state = state if state is not None else {}
        self.me = ""

    def whoami(self) -> tuple[bool, str]:
        status, value = self.request(f"{self.API}/users/@me", headers=self.headers, timeout=15)
        if status == 200:
            self.me = str(value.get("id"))
            return True, value.get("username", "")
        return False, f"Discord refused the token (HTTP {status or 'no connection'})."

    def _dm(self, user: str) -> str:
        channels = self.state.setdefault("dm", {})
        if user not in channels:
            status, value = self.request(f"{self.API}/users/@me/channels", method="POST", body={"recipient_id": user}, headers=self.headers, timeout=20)
            if status != 200:
                return ""
            channels[user] = str(value["id"])
        return channels[user]

    def poll(self, wait: int = 3) -> list[Inbound]:
        if not self.me:
            self.whoami()
        out = []
        for user in self.allow:
            channel = self._dm(user)
            if not channel:
                continue
            after = self.state.setdefault("after", {}).get(channel)
            query = f"?limit=20&after={after}" if after else "?limit=1"
            status, rows = self.request(f"{self.API}/channels/{channel}/messages{query}", headers=self.headers, timeout=20)
            if status != 200 or not isinstance(rows, list):
                continue
            for row in sorted(rows, key=lambda r: int(r["id"])):
                self.state["after"][channel] = row["id"]
                author = row.get("author") or {}
                images = [i for a in row.get("attachments") or [] if str(a.get("content_type", "")).split(";")[0] in IMAGE_TYPES
                          for i in [_image(a.get("filename", "image"), a["content_type"].split(";")[0], _download(a["url"]))] if i]
                if after and str(author.get("id")) != self.me and (row.get("content") or images):
                    out.append(Inbound(str(author.get("id")), channel, row.get("content") or "What's in this picture?", author.get("username", ""), images=images))
            if not after and not rows:
                self.state["after"][channel] = "0"
        time.sleep(wait)
        return out

    def send(self, chat: str, text: str, buttons: list[tuple[str, str]] | None = None) -> None:
        if buttons:
            text += "\n\nReply **yes** or **no**."
        self.request(f"{self.API}/channels/{chat}/messages", method="POST", body={"content": text[:1900]}, headers=self.headers, timeout=20)

    def acknowledge(self, button_id: str, text: str) -> None:
        return None

    def greet(self, user: str, text: str) -> bool:
        channel = self._dm(user)
        if channel:
            self.send(channel, text)
        return bool(channel)


class Slack:
    """The bot's direct messages with each allowed person, read with the Web API: no Socket Mode, no public address."""

    platform, label = "slack", "Slack"
    API = "https://slack.com/api"

    def __init__(self, token: str, allow: list[str], request: Callable[..., tuple[int, Any]] = _request, state: dict[str, Any] | None = None) -> None:
        self.token, self.allow, self.request = token, allow, request
        self.headers = {"Authorization": f"Bearer {token}"}
        self.state = state if state is not None else {}
        self.me = ""

    def whoami(self) -> tuple[bool, str]:
        status, value = self.request(f"{self.API}/auth.test", method="POST", body={}, headers=self.headers, timeout=15)
        if status == 200 and value.get("ok"):
            self.me = str(value.get("user_id"))
            return True, f"{value.get('user')} in {value.get('team')}"
        return False, f"Slack refused the token ({value.get('error') if isinstance(value, dict) else status})."

    def _dm(self, user: str) -> str:
        channels = self.state.setdefault("dm", {})
        if user not in channels:
            status, value = self.request(f"{self.API}/conversations.open", method="POST", body={"users": user}, headers=self.headers, timeout=20)
            if not (status == 200 and value.get("ok")):
                return ""
            channels[user] = str(value["channel"]["id"])
        return channels[user]

    def poll(self, wait: int = 3) -> list[Inbound]:
        if not self.me:
            self.whoami()
        out = []
        for user in self.allow:
            channel = self._dm(user)
            if not channel:
                continue
            oldest = self.state.setdefault("oldest", {}).get(channel)
            query = urllib.parse.urlencode({"channel": channel, "limit": 20, **({"oldest": oldest} if oldest else {"limit": 1})})
            status, value = self.request(f"{self.API}/conversations.history?{query}", headers=self.headers, timeout=20)
            if not (status == 200 and value.get("ok")):
                continue
            rows = sorted(value.get("messages") or [], key=lambda m: float(m["ts"]))
            for row in rows:
                self.state["oldest"][channel] = row["ts"]
                if oldest and row.get("user") == user and not row.get("bot_id"):
                    images = [i for f in row.get("files") or [] if f.get("mimetype") in IMAGE_TYPES
                              for i in [_image(f.get("name", "image"), f["mimetype"], _download(f["url_private"], self.headers))] if i]
                    out.append(Inbound(user, channel, row.get("text") or "What's in this picture?", user, images=images))
            if not oldest and not rows:
                self.state["oldest"][channel] = f"{time.time():.6f}"
        time.sleep(wait)
        return out

    def send(self, chat: str, text: str, buttons: list[tuple[str, str]] | None = None) -> None:
        if buttons:
            text += "\n\nReply *yes* or *no*."
        self.request(f"{self.API}/chat.postMessage", method="POST", body={"channel": chat, "text": text[:LIMIT]}, headers=self.headers, timeout=20)

    def acknowledge(self, button_id: str, text: str) -> None:
        return None

    def greet(self, user: str, text: str) -> bool:
        channel = self._dm(user)
        if channel:
            self.send(channel, text)
        return bool(channel)


def sender_vouched(message: Any, address: str) -> bool:
    """True when the receiving server recorded a DKIM or SPF pass for the sender's own domain."""
    domain = address.rsplit("@", 1)[-1].lower()
    for header in message.get_all("Authentication-Results") or []:
        text = " ".join(str(header).lower().split())
        if (f"dkim=pass" in text and (f"header.d={domain}" in text or f"header.i=@{domain}" in text)) or \
           ("spf=pass" in text and (f"smtp.mailfrom={address.lower()}" in text or f"smtp.mailfrom={domain}" in text)):
            return True
    return False


class Email:
    """An inbox Chaser reads over IMAP and answers over SMTP, both over TLS. Only vouched-for allowed senders count."""

    platform, label = "email", "Email"

    def __init__(self, password: str, config: dict[str, Any], allow: list[str], state: dict[str, Any] | None = None,
                 imap_factory: Callable[..., Any] | None = None, smtp_factory: Callable[..., Any] | None = None) -> None:
        import imaplib
        import smtplib

        self.password, self.config, self.allow = password, config, [a.lower() for a in allow]
        self.state = state if state is not None else {}
        self.imap_factory = imap_factory or (lambda: imaplib.IMAP4_SSL(config["imap_host"], int(config.get("imap_port") or 993)))
        self.smtp_factory = smtp_factory or (lambda: smtplib.SMTP_SSL(config["smtp_host"], int(config.get("smtp_port") or 465), timeout=30))
        self.threads = self.state.setdefault("threads", {})

    def whoami(self) -> tuple[bool, str]:
        try:
            box = self.imap_factory()
            box.login(self.config["address"], self.password)
            box.logout()
            return True, self.config["address"]
        except Exception as exc:  # imaplib raises its own error types
            return False, f"Couldn't sign in to {self.config.get('imap_host')}: {type(exc).__name__}"

    def poll(self, wait: int = 30) -> list[Inbound]:
        import email
        import email.utils

        out = []
        try:
            box = self.imap_factory()
            box.login(self.config["address"], self.password)
            box.select("INBOX")
            _, found = box.search(None, "UNSEEN")
            for number in (found[0] or b"").split()[:20]:
                _, parts = box.fetch(number, "(RFC822)")
                message = email.message_from_bytes(parts[0][1])
                address = email.utils.parseaddr(message.get("From", ""))[1].lower()
                if address not in self.allow:
                    continue  # left unread for the person; not ours to answer
                if not sender_vouched(message, address):
                    out.append(Inbound("unverified:" + address, address, ""))
                    continue
                text, images = "", []
                for part in message.walk():
                    kind = part.get_content_type()
                    if kind == "text/plain" and not text:
                        text = (part.get_payload(decode=True) or b"").decode(part.get_content_charset() or "utf-8", errors="replace")
                    elif kind in IMAGE_TYPES:
                        image = _image(part.get_filename() or "image", kind, part.get_payload(decode=True) or b"")
                        if image:
                            images.append(image)
                text = "\n".join(line for line in text.splitlines() if not line.startswith(">")).strip()
                self.threads[address] = {"subject": message.get("Subject", "Chaser"), "id": message.get("Message-ID", "")}
                out.append(Inbound(address, address, text or "What's in this picture?", address, images=images))
            box.logout()
        except Exception as exc:  # a mail hiccup must not stop the loop
            out.append(Inbound("error", "", f"{type(exc).__name__}"))
        time.sleep(wait)
        return [m for m in out if m.user != "error"]

    def send(self, chat: str, text: str, buttons: list[tuple[str, str]] | None = None) -> None:
        from email.message import EmailMessage

        thread = self.threads.get(chat, {})
        message = EmailMessage()
        subject = thread.get("subject") or "Chaser"
        message["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        message["From"], message["To"] = self.config["address"], chat
        if thread.get("id"):
            message["In-Reply-To"] = message["References"] = thread["id"]
        if buttons:
            text += f"\n\nTo decide, reply with yes {buttons[0][1].split(':')[-1][:8]} or no {buttons[0][1].split(':')[-1][:8]}."
        message.set_content(text)
        with self.smtp_factory() as server:
            server.login(self.config["address"], self.password)
            server.send_message(message)

    def acknowledge(self, button_id: str, text: str) -> None:
        return None


# --- The door ------------------------------------------------------------------------

@dataclass
class Bridge:
    """Turns messages into sessions and sessions back into messages, one conversation per chat."""

    adapter: Any
    allow: list[str]
    call: Callable[[str, str, dict[str, Any] | None], tuple[int, Any]]
    reviewer: str = ""
    log: Callable[[str], None] = lambda _line: None
    state: dict[str, Any] = field(default_factory=dict)

    @property
    def signer(self) -> str:
        return f"{self.reviewer or 'local_operator'} ({self.adapter.label})"

    def chats(self) -> dict[str, dict[str, Any]]:
        return self.state.setdefault("chats", {})

    def handle(self, message: Inbound) -> None:
        if message.user.startswith("unverified:"):
            self.log(f"{self.adapter.label}: ignored mail claiming to be {message.user[11:]}: its server didn't vouch for the sender (no DKIM or SPF pass)")
            return
        if message.user not in self.allow:
            self.log(f"{self.adapter.label}: ignored a message from {message.user}, who isn't on the allowlist")
            return
        chat = self.chats().setdefault(message.chat, {"session": None, "seen": 0, "asked": None})
        if message.button:
            self._button(message, chat)
            return
        text = message.text.strip()
        lowered = text.lower()
        if lowered in {"/start", "/help"}:
            self.adapter.send(message.chat, "Chaser here. Tell me what you need. /new starts fresh, /waiting shows what needs you, "
                                            "/stop stops the current task, /stopall stops everything. Send a photo to show me something. I'll ask before anything leaves your computer.")
            return
        if lowered == "/new":
            chat.update(session=None, seen=0, asked=None)
            self.adapter.send(message.chat, "Fresh conversation. What do you need?")
            return
        if lowered == "/stop" and chat["session"]:
            status, _ = self.call("POST", f"/v1/agent/sessions/{chat['session']}/cancel", {})
            self.adapter.send(message.chat, "Stopped." if status == 202 else "Nothing to stop.")
            return
        if lowered == "/stopall":
            from chaser_agent.chaser_work import stop_everything

            stopped = stop_everything(self.call)
            self.adapter.send(message.chat, f"Stopped {len(stopped)} task(s)." if stopped else "Nothing was running.")
            return
        if lowered == "/waiting":
            self._waiting(message.chat)
            return
        pending = self._pending(chat)
        first, _, rest = lowered.partition(" ")
        if pending and pending.get("kind") == "approval" and (first in YES or first in NO):
            # Email waits longer and threads cross, so there the answer must carry the digest's start.
            if self.adapter.platform == "email" and not (rest.strip() and str(pending.get("digest", "")).startswith(rest.strip()[:8])):
                self.adapter.send(message.chat, f"Reply with yes {str(pending.get('digest', ''))[:8]} or no {str(pending.get('digest', ''))[:8]} so I know which request you mean.")
                return
            self._decide(message.chat, chat, pending, "approve" if first in YES else "reject")
            return
        if pending and pending.get("kind") == "question":
            options = pending.get("options") or []
            answer = options[int(text) - 1] if text.isdecimal() and 1 <= int(text) <= len(options) else text
            status, value = self.call("POST", f"/v1/agent/sessions/{chat['session']}/answers", {"question_id": pending["id"], "answer": answer})
            if status != 202:
                self.adapter.send(message.chat, f"That didn't go through: {self._error(value)}")
            return
        extra = {"images": message.images} if message.images else {}
        if chat["session"]:
            status, value = self.call("POST", f"/v1/agent/sessions/{chat['session']}/messages", {"message": text, **extra})
            if status == 409:
                self.adapter.send(message.chat, "I'm still on the last task. Answer it, or send /stop.")
                return
        else:
            status, value = self.call("POST", "/v1/agent/sessions", {"message": text, "reasoner": "auto", **extra})
            if status == 201:
                chat.update(session=value["id"], seen=0, asked=None)
        if status not in {201, 202}:
            self.adapter.send(message.chat, f"I couldn't start that: {self._error(value)}")

    def _pending(self, chat: dict[str, Any]) -> dict[str, Any] | None:
        if not chat.get("session"):
            return None
        status, snap = self.call("GET", f"/v1/agent/sessions/{chat['session']}", None)
        return snap.get("pending") if status == 200 and snap.get("status") in WAITING else None

    def _button(self, message: Inbound, chat: dict[str, Any]) -> None:
        kind, _, rest = message.button.partition(":")
        approval_id, _, digest = rest.partition(":")
        pending = self._pending(chat)
        if not pending or pending.get("id") != approval_id or not str(pending.get("digest", "")).startswith(digest):
            self.adapter.acknowledge(message.button_id, "That request isn't waiting any more; nothing was decided.")
            return
        self._decide(message.chat, chat, pending, "approve" if kind == "y" else "reject", button_id=message.button_id)

    def _decide(self, where: str, chat: dict[str, Any], pending: dict[str, Any], decision: str, *, button_id: str = "") -> None:
        status, value = self.call("POST", f"/v1/agent/sessions/{chat['session']}/approvals", {
            "approval_id": pending["id"], "digest": pending["digest"], "decision": decision, "decided_by": self.signer})
        word = "Approved" if decision == "approve" else "Rejected"
        text = f"{word}, signed {self.signer}." if status == 202 else f"That didn't go through: {self._error(value)}"
        self.adapter.acknowledge(button_id, text)
        self.adapter.send(where, text)

    def _waiting(self, where: str) -> None:
        _, value = self.call("GET", "/v1/agent/sessions", None)
        rows = [r for r in (value or {}).get("sessions") or [] if r.get("status") in WAITING]
        self.adapter.send(where, "Nothing is waiting for you." if not rows else
                          "Waiting for you:\n" + "\n".join(f"• {str(r.get('title') or '').splitlines()[0][:80]}" for r in rows[:10]))

    def follow(self) -> None:
        """Forward what each chat's session did since last time: steps briefly, questions, approvals, the answer."""
        for where, chat in self.chats().items():
            if not chat.get("session"):
                continue
            status, page = self.call("GET", f"/v1/agent/sessions/{chat['session']}/events?after={chat['seen']}", None)
            if status != 200:
                continue
            steps = []
            for event in page.get("events") or []:
                chat["seen"] = event["seq"]
                data, kind = event.get("data") or {}, event.get("type")
                if kind == "tool_started" and data.get("tool") != "update_plan":
                    steps.append(str(data.get("tool")))
                elif kind == "turn_finished":
                    if steps:
                        self.adapter.send(where, "Steps: " + ", ".join(steps))
                        steps = []
                    self.adapter.send(where, str(data.get("answer") or data.get("error") or "Done."))
            if steps:
                self.adapter.send(where, "Working: " + ", ".join(steps))
            pending = self._pending(chat)
            if pending and pending.get("id") != chat.get("asked"):
                chat["asked"] = pending.get("id")
                if pending.get("kind") == "approval":
                    args = json.dumps(pending.get("args") or {}, ensure_ascii=False, indent=1)
                    digest = str(pending.get("digest", ""))
                    self.adapter.send(where, f"Needs your yes: {pending.get('tool')}\n{args[:1500]}\n\ndigest {digest[:16]}…, signed {self.signer}",
                                      buttons=[("Yes", f"y:{pending['id']}:{digest[:16]}"), ("No", f"n:{pending['id']}:{digest[:16]}")])
                else:
                    options = pending.get("options") or []
                    lines = [f"Chaser asks: {pending.get('question')}", *(f"{n}. {o}" for n, o in enumerate(options, 1))]
                    self.adapter.send(where, "\n".join(lines))

    @staticmethod
    def _error(value: Any) -> str:
        return (((value or {}).get("error") or {}).get("message") or "no answer") if isinstance(value, dict) else str(value)


# --- Running them ---------------------------------------------------------------------

def adapter_for(platform: str, settings: dict[str, Any], state: dict[str, Any]) -> Any:
    token = load_token(platform)
    value = (settings.get("channels") or {}).get(platform, {})
    allow = [str(x) for x in value.get("allow") or []]
    if platform == "telegram":
        return Telegram(token)
    if platform == "slack":
        return Slack(token, allow, state=state.setdefault("slack_adapter", {}))
    if platform == "email":
        return Email(token, value, allow, state=state.setdefault("email_adapter", {}))
    return Discord(token, allow, state=state.setdefault("discord", {}))


def _state_path(settings: dict[str, Any]) -> Path:
    return Path(settings["data_dir"]) / "channels" / "state.json"


def run(settings: dict[str, Any], call: Callable[[str, str, dict[str, Any] | None], tuple[int, Any]], *, log: Callable[[str], None] = print,
        stop: threading.Event | None = None) -> None:
    """Serve every configured channel until stopped. State (offsets, which chat is which session) survives restarts."""
    stop = stop or threading.Event()
    path = _state_path(settings)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    bridges = []
    for platform, value in configured(settings).items():
        if not load_token(platform):
            log(f"{PLATFORMS[platform]['label']}: no token saved; run chaser channels add {platform}")
            continue
        adapter = adapter_for(platform, settings, state)
        if isinstance(adapter, Telegram):
            adapter.offset = int(state.get("telegram_offset") or 0)
        bridges.append(Bridge(adapter, [str(x) for x in value["allow"]], call, settings.get("reviewer") or "", log, state.setdefault(platform, {})))
        log(f"{adapter.label}: listening for {len(value['allow'])} allowed account(s)")
    if not bridges:
        return

    def serve(bridge: Bridge) -> None:
        while not stop.is_set():
            try:
                for message in bridge.adapter.poll():
                    bridge.handle(message)
                bridge.follow()
                if isinstance(bridge.adapter, Telegram):
                    state["telegram_offset"] = bridge.adapter.offset
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(state), encoding="utf-8")
            except Exception as exc:  # a channel hiccup must not take Chaser down
                log(f"{bridge.adapter.label}: {type(exc).__name__}: {exc}")
                stop.wait(10)

    threads = [threading.Thread(target=serve, args=(b,), daemon=True, name=f"chaser-{b.adapter.platform}") for b in bridges]
    for thread in threads:
        thread.start()
    while not stop.is_set() and any(t.is_alive() for t in threads):
        stop.wait(1)


def service_caller(settings: dict[str, Any]) -> Callable[[str, str, dict[str, Any] | None], tuple[int, Any]]:
    import argparse

    from chaser_agent import agent_cli

    args = argparse.Namespace(data_dir=str(settings["data_dir"]), port=int(settings["port"]))
    return lambda method, route, body=None: agent_cli._call(args, method, route, body)


def start_background(settings: dict[str, Any], log: Callable[[str], None]) -> threading.Thread | None:
    """Used by the gateway's supervisor: serve the channels next to the service, if any are set up."""
    if not configured(settings):
        return None
    thread = threading.Thread(target=run, args=(settings, service_caller(settings)), kwargs={"log": log}, daemon=True, name="chaser-channels")
    thread.start()
    return thread
