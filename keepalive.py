"""Ryhavean Userbot — Render + UptimeRobot üçün keep-alive veb server.

Render pulsuz (free) servisində layihənin yatmaması üçün sadə HTTP server
qaldırılır. UptimeRobot bu ünvana hər 5 dəqiqədən bir sorğu göndərməklə
botun 7/24 işləməsini təmin edir.

Yoxlama ünvanları:
    GET /        -> status səhifəsi
    GET /ping    -> "pong"
    GET /health  -> JSON status
"""

from __future__ import annotations

import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

logger = logging.getLogger("userbot")

_START_TIME = time.time()


def _uptime() -> str:
    seconds = int(time.time() - _START_TIME)
    gun, qaliq = divmod(seconds, 86400)
    saat, qaliq = divmod(qaliq, 3600)
    deqiqe, saniye = divmod(qaliq, 60)
    return f"{gun}g {saat}s {deqiqe}d {saniye}san"


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str, content_type: str = "text/html; charset=utf-8"):
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):  # noqa: N802
        try:
            from config import clients
            aktiv = len(clients)
        except Exception:
            aktiv = 0

        if self.path.rstrip("/") in ("/ping",):
            return self._send(200, "pong", "text/plain; charset=utf-8")

        if self.path.rstrip("/") in ("/health",):
            return self._send(
                200,
                json.dumps({
                    "status": "işləyir",
                    "aktiv_userbotlar": aktiv,
                    "işləmə_müddəti": _uptime(),
                }, ensure_ascii=False),
                "application/json; charset=utf-8",
            )

        return self._send(200, f"""<!doctype html>
<html lang="az">
<head><meta charset="utf-8"><title>Ryhavean Userbot</title></head>
<body style="font-family:sans-serif;background:#0f1117;color:#e6e6e6;text-align:center;padding:60px">
  <h1>🚀 Ryhavean Userbot</h1>
  <p>Sistem aktiv şəkildə işləyir.</p>
  <p>Aktiv userbotlar: <b>{aktiv}</b></p>
  <p>İşləmə müddəti: <b>{_uptime()}</b></p>
  <p><a style="color:#6ea8fe" href="https://t.me/ryhaveanupdates">Yeniliklər kanalı</a> ·
     <a style="color:#6ea8fe" href="https://t.me/RyhaveanTeam">İcma qrupu</a></p>
</body></html>""")

    def do_HEAD(self):  # noqa: N802
        self._send(200, "")

    def log_message(self, fmt, *args):  # serveri səssiz saxlayırıq
        return


def start_keepalive(port: int = 8080) -> None:
    """Keep-alive serverini arxa planda işə salır."""
    def _run():
        try:
            server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
            logger.info("Keep-alive server işə düşdü: 0.0.0.0:%s", port)
            server.serve_forever()
        except Exception as exc:
            logger.error("Keep-alive server xətası: %s", exc)

    threading.Thread(target=_run, daemon=True).start()


def start_self_ping(url: str, interval: int = 240) -> None:
    """UptimeRobot dəstəyi: layihə öz ünvanına periodik sorğu göndərir.

    UptimeRobot (https://uptimerobot.com) üzərində HTTP(s) monitoru yaradıb
    `<layihə-ünvanı>/ping` ünvanını 5 dəqiqəlik intervalla yoxlamaq kifayətdir.
    Bu funksiya isə əlavə təhlükəsizlik qatıdır — monitor işləmədikdə belə
    servisin yatmasının qarşısını alır.
    """
    if not url:
        logger.info("PING_URL təyin edilməyib — öz-özünə ping deaktivdir.")
        return

    target = url.rstrip("/") + "/ping"

    def _run():
        import urllib.request

        while True:
            time.sleep(max(30, interval))
            try:
                with urllib.request.urlopen(target, timeout=20) as resp:
                    logger.debug("Self-ping %s -> %s", target, resp.status)
            except Exception as exc:
                logger.debug("Self-ping alınmadı (%s): %s", target, exc)

    threading.Thread(target=_run, daemon=True).start()
    logger.info("Öz-özünə ping aktivdir: %s (hər %s san)", target, interval)
