# Kong API Bundle — 損害保険ドメイン

Kong Gateway Enterprise 3.15 + Kong Konnect を前段に置き、損害保険会社を想定した
6つのサンプルAPIサービスを稼働させるデモ環境です。まず Docker Compose で動作し、
後工程で AWS ECS にも対応します。すべて日本語・日本のデータフォーマット
(郵便番号・マイナンバー・電話番号など)に準拠しています。

## サービス構成

| サービス | 役割 | テストデータ | ローカルポート | Kong Route |
|---|---|---|---|---|
| **product** | 商品マスタ | 5件 | 8001 | `/product` |
| **customer** | 顧客 | 100件 | 8002 | `/customer` |
| **simulation** | 保険料試算(ステートレス) | – | 8003 | `/simulation` |
| **application** | 申込 | 300件（成立200／未成立100） | 8004 | `/application` |
| **policy** | 契約 | 200件 | 8005 | `/policy` |
| **claim** | 保険金請求 | 50件 | 8006 | `/claim` |

商品ラインナップ（損害保険）: 火災保険 / 自動車保険 / 傷害保険 / 医療保険（第三分野） / ペット保険。

テストデータは全サービスをまたいで参照整合性が取れています（申込→契約→請求の連鎖、
商品カテゴリと請求種別の整合など）。詳細は [docs/DATA.md](docs/DATA.md) を参照してください。

## クイックスタート（Docker Compose）

```bash
# 1. テストデータを生成（初回のみ。data/seed/*.json が生成される）
python3 scripts/generate_test_data.py

# 2. 6サービスを起動
docker compose up -d --build

# 3. 動作確認
curl http://localhost:8001/products
curl http://localhost:8002/customers?limit=5
curl -X POST http://localhost:8003/simulations \
  -H 'content-type: application/json' \
  -d '{"product_id":"PRD-002","birth_date":"1990-01-01","sum_insured":3000000}'
```

各サービスの Swagger UI は `http://localhost:<port>/docs` で確認できます。

## Kong Konnect 連携

Service / Route の宣言的設定は [deck/kong.yaml](deck/kong.yaml) にあり、decK で Konnect に反映します。
現時点では **Service と Route のみ**（認証等のプラグインは今後追加）。

```bash
export KONNECT_PAT=<Konnect Personal Access Token>
deck gateway sync deck/kong.yaml \
  --konnect-token "$KONNECT_PAT" \
  --konnect-addr https://us.api.konghq.com \
  --konnect-control-plane-name kong-insurance-demo
```

Kong Gateway (Data Plane) を Konnect に接続してプロキシ経由でアクセスする手順は
[docs/INSTRUCTIONS.md](docs/INSTRUCTIONS.md) を参照してください。

## ドキュメント

- [docs/DATA.md](docs/DATA.md) — データモデル定義と設計判断の記録
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 全体構成・技術選定・ディレクトリ構成
- [docs/INSTRUCTIONS.md](docs/INSTRUCTIONS.md) — 環境構築の詳細手順（ローカル / Konnect / ECS）
- [CLAUDE.md](CLAUDE.md) — 本リポジトリでの取り決め・作業方針

## 技術スタック

- **バックエンド**: Python 3.13 / FastAPI（OpenAPI 3.1 を自動生成）
- **API Gateway**: Kong Gateway Enterprise 3.15（Konnect Hybrid mode / Data Plane）
- **宣言的管理**: decK
- **実行環境**: Docker Compose（ローカル）→ AWS ECS（後工程）

## ディレクトリ構成

```
.
├── common/                # 全サービス共通モジュール（日本フォーマット・商品定義・保険料計算・ストア）
├── services/              # 6サービスのFastAPI実装（各 app/ + 共通 Dockerfile）
├── scripts/               # テストデータ生成・OpenAPI書き出し・Konnect DP接続
├── data/seed/             # 生成されたテストデータ（JSON）
├── deck/                  # Kong 宣言的設定（decK）
├── docs/                  # ドキュメント
└── docker-compose.yml
```

## ライセンス / 注意事項

- 本リポジトリのデータはすべて **架空のダミーデータ** です。マイナンバー・氏名・住所・
  口座情報等は形式的に正しい値を機械生成したもので、実在の個人とは一切関係ありません。
