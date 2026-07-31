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

## Kong Konnect 連携（Terraform）

Konnect の **Control Plane・Service・Route・Data Plane 証明書** はすべて Terraform で管理します
（[terraform/konnect/](terraform/konnect/)）。現時点では **Service と Route のみ**（認証等のプラグインは今後追加）。

```bash
cd terraform/konnect
export TF_VAR_konnect_pat=<Konnect Personal Access Token>
terraform init
terraform apply
```

`terraform apply` により以下が作成されます:

- Control Plane `kong-insurance-demo`
- 6つの Service と Route（`/product` 〜 `/claim`）
- Kong Data Plane 接続用の自己署名証明書（リポジトリルートの `certs/` に出力し、Konnect に登録）

## デプロイ方式（Docker Compose / AWS ECS）

同じ6サービス + Kong DP を、**2通りの方式**で動かせます（どちらかが本番専用ということはなく、
選択できるサンプルです）:

- **Docker Compose** — 上記クイックスタート、および `docker compose --profile konnect up` で DP も起動
- **AWS ECS (Fargate)** — [terraform/ecs/](terraform/ecs/) で VPC・ECS・ALB・DP を構築、`scripts/build_push_ecr.sh` でイメージを push

いずれも詳細な手順は [docs/INSTRUCTIONS.md](docs/INSTRUCTIONS.md) を参照してください。

## ドキュメント

- [docs/DATA.md](docs/DATA.md) — データモデル定義と設計判断の記録
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 全体構成・技術選定・ディレクトリ構成
- [docs/INSTRUCTIONS.md](docs/INSTRUCTIONS.md) — 環境構築の詳細手順（ローカル / Konnect / ECS）
- [CLAUDE.md](CLAUDE.md) — 本リポジトリでの取り決め・作業方針

## 技術スタック

- **バックエンド**: Python 3.13 / FastAPI（OpenAPI 3.1 を自動生成）
- **API Gateway**: Kong Gateway Enterprise 3.15（Konnect Hybrid mode / Data Plane）
- **IaC / 宣言的管理**: Terraform（Kong/konnect provider で Control Plane・Service・Route・DP証明書を管理）
- **実行環境**: Docker Compose（ローカル）→ AWS ECS（後工程）

## ディレクトリ構成

```
.
├── common/                # 全サービス共通モジュール（日本フォーマット・商品定義・保険料計算・ストア）
├── services/              # 6サービスのFastAPI実装（各 app/ + 共通 Dockerfile）
├── scripts/               # テストデータ生成・OpenAPI書き出し・ECRビルド/push
├── data/seed/             # 生成されたテストデータ（JSON）
├── terraform/
│   ├── konnect/           # Konnect の IaC（Control Plane・Service・Route・DP証明書）
│   └── ecs/               # AWS ECS の IaC（VPC・ECS・ALB・Kong DP）
├── docs/                  # ドキュメント
└── docker-compose.yml     # Docker Compose 方式
```

## ライセンス / 注意事項

- 本リポジトリのデータはすべて **架空のダミーデータ** です。マイナンバー・氏名・住所・
  口座情報等は形式的に正しい値を機械生成したもので、実在の個人とは一切関係ありません。
