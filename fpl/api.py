"""Thin, cached client for the public FPL API.

Every response is written to ``fpl/.cache/<date>/`` so a run can be replayed
offline (``--offline``) and so the audit always states exactly which data it used.
"""
from __future__ import annotations

import json
import os
import time
from datetime import date
from pathlib import Path

import requests

BASE = "https://fantasy.premierleague.com/api"
CACHE_ROOT = Path(__file__).resolve().parent / ".cache"
HEADERS = {"User-Agent": "Mozilla/5.0 (fpl-engine)"}


class FPLClient:
    def __init__(self, offline_dir: str | None = None, max_age_s: int = 1800):
        self.offline = Path(offline_dir) if offline_dir else None
        self.cache = self.offline or CACHE_ROOT / date.today().isoformat()
        self.max_age_s = max_age_s
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _path(self, endpoint: str) -> Path:
        return self.cache / (endpoint.strip("/").replace("/", "__").replace("?", "_") + ".json")

    def get(self, endpoint: str):
        path = self._path(endpoint)
        if self.offline:
            return json.loads(path.read_text(encoding="utf-8"))
        if path.exists() and time.time() - path.stat().st_mtime < self.max_age_s:
            return json.loads(path.read_text(encoding="utf-8"))
        for attempt in range(4):
            try:
                route, _, query = endpoint.strip("/").partition("?")
                url = f"{BASE}/{route}/" + (f"?{query}" if query else "")
                r = self.session.get(url, timeout=30)
                r.raise_for_status()
                break
            except requests.RequestException:
                if attempt == 3:
                    raise
                time.sleep(2 ** (attempt + 1))
        data = r.json()
        os.makedirs(path.parent, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return data

    # Convenience wrappers ---------------------------------------------------
    def bootstrap(self):
        return self.get("bootstrap-static")

    def fixtures(self):
        return self.get("fixtures")

    def entry(self, team_id: int):
        return self.get(f"entry/{team_id}")

    def history(self, team_id: int):
        return self.get(f"entry/{team_id}/history")

    def transfers(self, team_id: int):
        return self.get(f"entry/{team_id}/transfers")

    def picks(self, team_id: int, gw: int):
        return self.get(f"entry/{team_id}/event/{gw}/picks")

    def league(self, league_id: int, page: int = 1):
        return self.get(f"leagues-classic/{league_id}/standings?page_standings={page}")
