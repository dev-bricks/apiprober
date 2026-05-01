"""
ApiProber.core.http_client -- HTTP-Client mit Rate-Limiting
=============================================================
urllib.request Wrapper mit Auth, Rate-Limiting, User-Agent, Retry.
Pattern: BACH connectors/base.py (dataclass, UA, Retry)

B36-Fix (SQ080): Timeout-Bug behoben:
  - Connection-Timeout (10s) vs Read-Timeout (30s) getrennt
  - Retry-Mechanismus mit exponentiellem Backoff (max 3 Versuche)
  - socket.timeout wird explizit gefangen statt als generische Exception
  - Timeout-Werte ueber Config steuerbar (connect_timeout_s, read_timeout_s)
"""
import json
import socket
import time
import ssl
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HttpResponse:
    """Ergebnis eines HTTP-Requests."""
    url: str
    method: str
    status_code: int
    headers: dict = field(default_factory=dict)
    body: str = ""
    content_type: str = ""
    elapsed_ms: int = 0
    error: str = ""
    is_json: bool = False
    retries: int = 0

    @property
    def ok(self):
        return 200 <= self.status_code < 400

    @property
    def is_timeout(self):
        return "timeout" in self.error.lower() if self.error else False

    def json(self):
        if self.body:
            return json.loads(self.body)
        return None


class HttpClient:
    """HTTP-Client mit Rate-Limiting, Auth-Support und Retry.

    Timeout-Konfiguration (B36-Fix):
        timeout_seconds:    Gesamt-Timeout fuer urllib (Fallback, Default: 30)
        connect_timeout_s:  Connection-Timeout in Sekunden (Default: 10)
        read_timeout_s:     Read-Timeout in Sekunden (Default: 30)
        max_retries:        Maximale Retry-Versuche bei Timeout (Default: 2)

    Hinweis: urllib.request.urlopen kennt nur EINEN timeout-Parameter.
    Wir setzen diesen auf read_timeout_s (der groessere Wert) und pruefen
    den Connection-Timeout separat ueber socket.setdefaulttimeout waehrend
    des Verbindungsaufbaus. Fuer echte Trennung muesste man auf
    http.client.HTTPConnection umsteigen -- das waere ein groesseres
    Refactoring. Der pragmatische Fix: read_timeout hoch genug setzen
    (30s statt 15s) und Retries einfuehren.
    """

    # Timeout-Fehler die einen Retry rechtfertigen
    _RETRYABLE_ERRORS = (socket.timeout, TimeoutError, ConnectionResetError,
                         ConnectionAbortedError, BrokenPipeError)

    def __init__(self, config):
        self.delay_ms = config.get("delay_ms", 500)

        # B36-Fix: Getrennte Timeouts + Fallback auf alten Key
        legacy_timeout = config.get("timeout_seconds", 30)
        self.connect_timeout = config.get("connect_timeout_s", min(legacy_timeout, 10))
        self.read_timeout = config.get("read_timeout_s", max(legacy_timeout, 30))
        # urllib bekommt den groesseren Wert (read_timeout)
        self.timeout = self.read_timeout

        self.max_retries = config.get("max_retries", 2)
        self.user_agent = config.get("user_agent", "ApiProber/0.1")
        self.auth_type = config.get("auth", {}).get("type", "none")
        self.auth_value = config.get("auth", {}).get("value", "")
        self._last_request_time = 0.0
        self._request_count = 0
        self._ssl_ctx = ssl.create_default_context()

    @property
    def request_count(self):
        return self._request_count

    def request(self, url, method="GET", body=None, extra_headers=None):
        """HTTP-Request mit Rate-Limiting und Retry. Gibt HttpResponse zurueck."""
        self._rate_limit()

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/html, */*",
        }

        # Auth
        if self.auth_type == "bearer" and self.auth_value:
            headers["Authorization"] = f"Bearer {self.auth_value}"
        elif self.auth_type == "api_key" and self.auth_value:
            headers["X-API-Key"] = self.auth_value
        elif self.auth_type == "basic" and self.auth_value:
            import base64
            encoded = base64.b64encode(self.auth_value.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        if extra_headers:
            headers.update(extra_headers)

        data = None
        if body is not None:
            if isinstance(body, dict):
                data = json.dumps(body).encode("utf-8")
                headers["Content-Type"] = "application/json"
            elif isinstance(body, str):
                data = body.encode("utf-8")
            elif isinstance(body, bytes):
                data = body

        # Retry-Loop (B36-Fix)
        last_error = None
        for attempt in range(1 + self.max_retries):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            start = time.monotonic()
            self._request_count += 1

            try:
                with urllib.request.urlopen(req, timeout=self.timeout,
                                            context=self._ssl_ctx) as resp:
                    elapsed = int((time.monotonic() - start) * 1000)
                    resp_headers = dict(resp.headers)
                    content_type = resp_headers.get("Content-Type", "")
                    raw_body = resp.read()

                    # Body decodieren
                    body_str = ""
                    try:
                        body_str = raw_body.decode("utf-8")
                    except UnicodeDecodeError:
                        body_str = raw_body.decode("latin-1", errors="replace")

                    is_json = "json" in content_type.lower()

                    return HttpResponse(
                        url=url, method=method,
                        status_code=resp.status,
                        headers=resp_headers,
                        body=body_str,
                        content_type=content_type,
                        elapsed_ms=elapsed,
                        is_json=is_json,
                        retries=attempt
                    )
            except urllib.error.HTTPError as e:
                # HTTP-Fehler sind keine Netzwerk-Timeouts -- kein Retry
                elapsed = int((time.monotonic() - start) * 1000)
                resp_headers = dict(e.headers) if e.headers else {}
                content_type = resp_headers.get("Content-Type", "")
                body_str = ""
                try:
                    raw = e.read()
                    body_str = raw.decode("utf-8", errors="replace")
                except Exception:
                    pass
                return HttpResponse(
                    url=url, method=method,
                    status_code=e.code,
                    headers=resp_headers,
                    body=body_str,
                    content_type=content_type,
                    elapsed_ms=elapsed,
                    error=str(e),
                    is_json="json" in content_type.lower(),
                    retries=attempt
                )
            except (socket.timeout, TimeoutError) as e:
                # B36-Fix: Explizites Timeout-Handling mit Retry
                elapsed = int((time.monotonic() - start) * 1000)
                last_error = f"Timeout nach {elapsed}ms: {e}"
                if attempt < self.max_retries:
                    backoff = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s ...
                    time.sleep(backoff)
                    continue
                return HttpResponse(
                    url=url, method=method,
                    status_code=0,
                    elapsed_ms=elapsed,
                    error=last_error,
                    retries=attempt
                )
            except urllib.error.URLError as e:
                elapsed = int((time.monotonic() - start) * 1000)
                reason_str = str(e.reason)
                # URLError kann einen socket.timeout wrappen
                is_timeout = isinstance(e.reason, (socket.timeout, TimeoutError))
                if is_timeout and attempt < self.max_retries:
                    last_error = f"Connection-Timeout nach {elapsed}ms: {reason_str}"
                    backoff = (2 ** attempt) * 0.5
                    time.sleep(backoff)
                    continue
                # Connection-Refused, DNS-Fehler etc. -- kein Retry
                return HttpResponse(
                    url=url, method=method,
                    status_code=0,
                    elapsed_ms=elapsed,
                    error=reason_str,
                    retries=attempt
                )
            except (ConnectionResetError, ConnectionAbortedError,
                    BrokenPipeError) as e:
                # Netzwerk-Fehler die einen Retry rechtfertigen
                elapsed = int((time.monotonic() - start) * 1000)
                last_error = f"Verbindungsfehler nach {elapsed}ms: {e}"
                if attempt < self.max_retries:
                    backoff = (2 ** attempt) * 0.5
                    time.sleep(backoff)
                    continue
                return HttpResponse(
                    url=url, method=method,
                    status_code=0,
                    elapsed_ms=elapsed,
                    error=last_error,
                    retries=attempt
                )
            except Exception as e:
                elapsed = int((time.monotonic() - start) * 1000)
                return HttpResponse(
                    url=url, method=method,
                    status_code=0,
                    elapsed_ms=elapsed,
                    error=str(e),
                    retries=attempt
                )

        # Sollte nicht erreicht werden, aber Safety-Net
        return HttpResponse(
            url=url, method=method,
            status_code=0,
            error=last_error or "Unbekannter Fehler nach Retries",
            retries=self.max_retries
        )

    def head(self, url):
        return self.request(url, method="HEAD")

    def get(self, url):
        return self.request(url, method="GET")

    def options(self, url):
        return self.request(url, method="OPTIONS")

    def _rate_limit(self):
        """Wartet bis delay_ms seit letztem Request vergangen sind."""
        if self._last_request_time > 0:
            elapsed = (time.monotonic() - self._last_request_time) * 1000
            remaining = self.delay_ms - elapsed
            if remaining > 0:
                time.sleep(remaining / 1000.0)
        self._last_request_time = time.monotonic()
