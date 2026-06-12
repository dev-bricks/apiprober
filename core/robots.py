"""
ApiProber.core.robots -- robots.txt Respektierung
===================================================
Nutzt urllib.robotparser fuer Zugriffskontrolle.
"""
import urllib.robotparser
import urllib.request
import urllib.error


class RobotsChecker:
    """Prueft robots.txt Regeln fuer eine Base-URL."""

    def __init__(self, base_url, user_agent="ApiProber/0.1"):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self._parser = urllib.robotparser.RobotFileParser()
        self._loaded = False
        self._raw_text = ""
        # HTTP-Status wenn der robots.txt-Abruf serverseitig (5xx) scheiterte
        self.unavailable_status = None

    def load(self):
        """robots.txt laden und parsen. Gibt (success, raw_text) zurueck.

        Verhalten nach RFC 9309:
        - 2xx: Regeln parsen
        - 4xx (inkl. 404): kein robots.txt vorhanden -> alles erlaubt
        - 5xx: Server-Fehler -> konservativ ALLES gesperrt (disallow all),
          unavailable_status wird gesetzt
        - Netzwerkfehler: wie "kein robots.txt" (alles erlaubt)
        """
        robots_url = f"{self.base_url}/robots.txt"
        try:
            req = urllib.request.Request(robots_url)
            req.add_header("User-Agent", self.user_agent)
            with urllib.request.urlopen(req, timeout=10) as resp:
                self._raw_text = resp.read().decode("utf-8", errors="replace")
            self._parser.parse(self._raw_text.splitlines())
            self._loaded = True
            return True, self._raw_text
        except urllib.error.HTTPError as e:
            self._parser.parse([])
            if e.code >= 500:
                # RFC 9309: bei Server-Fehlern sind die Regeln unbekannt
                # -> konservativ alles sperren statt "alles erlaubt"
                self._parser.disallow_all = True
                self.unavailable_status = e.code
            # 4xx (inkl. 404) = kein robots.txt = alles erlaubt
            self._loaded = True
            return False, ""
        except Exception:
            # Netzwerkfehler (DNS, Timeout, ...): kein robots.txt = alles erlaubt
            # parse([]) setzt mtime(), damit can_fetch() True liefert
            self._parser.parse([])
            self._loaded = True
            return False, ""

    def is_allowed(self, path):
        """Prueft ob ein Pfad erlaubt ist."""
        if not self._loaded:
            self.load()
        full_url = f"{self.base_url}{path}"
        return self._parser.can_fetch(self.user_agent, full_url)

    @property
    def raw_text(self):
        return self._raw_text

    @property
    def crawl_delay(self):
        """Crawl-Delay aus robots.txt (oder None)."""
        if not self._loaded:
            self.load()
        try:
            delay = self._parser.crawl_delay(self.user_agent)
            return delay
        except Exception:
            return None
