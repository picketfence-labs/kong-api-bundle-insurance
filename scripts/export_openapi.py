#!/usr/bin/env python3
"""各サービスのFastAPIアプリからOpenAPI仕様(YAML)を書き出す。

書き出し先は services/<service>/openapi.yaml。Kong Konnect への API 仕様
登録(Dev Portal / Spec)や decK 設定の参考に使う。

使い方: python3 scripts/export_openapi.py
"""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import yaml
except ModuleNotFoundError:
    print("PyYAML が必要です: pip install pyyaml", file=sys.stderr)
    raise

SERVICES = ["product", "customer", "simulation", "application", "policy", "claim"]

def main():
    for service in SERVICES:
        module = importlib.import_module(f"services.{service}.app.main")
        schema = module.app.openapi()
        schema["servers"] = [
            {
                "url": f"http://{service}.insurance.svc.cluster.local:8000",
                "description": "Kubernetes クラスタ内の Service",
            },
        ]
        out_path = ROOT / "services" / service / "openapi.yaml"
        out_path.write_text(
            yaml.safe_dump(schema, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        print(f"wrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
