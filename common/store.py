"""JSONシードファイルをメモリ上にロードして簡易CRUDを提供する共有ストア。

product/customer/application/policy/claim の5サービスはいずれも「起動時に
data/seed/*.json を読み込み、プロセス内のメモリで保持しながらCRUDを提供する」
という同一の構造を持つため、共通実装として切り出す。永続化はプロセス内のみ
(再起動でシードデータへリセットされる)。
"""
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from common.jp_data import format_id

_JST = timezone(timedelta(hours=9))
_REPO_ROOT = Path(__file__).resolve().parent.parent


def now_jst() -> str:
    return datetime.now(_JST).strftime("%Y-%m-%dT%H:%M:%S+09:00")


def resolve_seed_path(service_name: str) -> Path:
    """シードファイルのパスを解決する。

    環境変数 SEED_FILE が指定されていればそれを、なければリポジトリの
    data/seed/<service_name>.json を使う(ローカル開発用フォールバック)。
    """
    env = os.getenv("SEED_FILE")
    if env:
        return Path(env)
    return _REPO_ROOT / "data" / "seed" / f"{service_name}.json"


class JsonStore:
    def __init__(self, seed_path: Path, id_field: str, id_prefix: str, id_width: int = 6):
        self.id_field = id_field
        self.id_prefix = id_prefix
        self.id_width = id_width
        self._records: dict[str, dict[str, Any]] = {}
        self._next_seq = 1
        self._load(seed_path)

    def _load(self, seed_path: Path) -> None:
        raw = json.loads(seed_path.read_text(encoding="utf-8"))
        max_seq = 0
        for record in raw:
            rec_id = record[self.id_field]
            self._records[rec_id] = record
            match = re.search(r"(\d+)$", rec_id)
            if match:
                max_seq = max(max_seq, int(match.group(1)))
        self._next_seq = max_seq + 1

    def list(self, filters: dict[str, Any] | None = None, skip: int = 0, limit: int = 50):
        items = list(self._records.values())
        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                items = [r for r in items if r.get(key) == value]
        total = len(items)
        return total, items[skip: skip + limit]

    def get(self, record_id: str) -> dict[str, Any] | None:
        return self._records.get(record_id)

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        new_id = format_id(self.id_prefix, self._next_seq, self.id_width)
        self._next_seq += 1
        record = {self.id_field: new_id, **payload}
        self._records[new_id] = record
        return record

    def update(self, record_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        existing = self._records.get(record_id)
        if existing is None:
            return None
        updated = {**existing, **{k: v for k, v in payload.items() if v is not None}}
        self._records[record_id] = updated
        return updated

    def delete(self, record_id: str) -> bool:
        return self._records.pop(record_id, None) is not None
