# 環境構築手順

## 0. 前提ツール

- Docker / Docker Compose v2
- Python 3.11+（テストデータ生成・OpenAPI書き出し用。3.13 で確認済み）
- [Terraform](https://developer.hashicorp.com/terraform) v1.5+（Konnect 連携）
- Kong Konnect アカウントと Personal Access Token（PAT）

---

## 1. テストデータの生成

初回、またはデータモデルを変更したときに実行します。乱数シードを固定しているため、
再実行しても同じデータが生成されます。

```bash
# 依存(Faker/PyYAML)をインストール
python3 -m pip install -r scripts/requirements.txt

# data/seed/*.json を生成
python3 scripts/generate_test_data.py
```

出力: `data/seed/{product,customer,application,policy,claim}.json`
（simulation は永続データを持たないためファイルなし）

---

## 2. ローカル実行（Docker Compose）

```bash
docker compose up -d --build
```

| サービス | URL | Swagger UI |
|---|---|---|
| product | http://localhost:8001 | http://localhost:8001/docs |
| customer | http://localhost:8002 | http://localhost:8002/docs |
| simulation | http://localhost:8003 | http://localhost:8003/docs |
| application | http://localhost:8004 | http://localhost:8004/docs |
| policy | http://localhost:8005 | http://localhost:8005/docs |
| claim | http://localhost:8006 | http://localhost:8006/docs |

動作確認例:

```bash
curl http://localhost:8001/products
curl "http://localhost:8005/policies?status=有効&limit=3"
curl -X POST http://localhost:8003/simulations \
  -H 'content-type: application/json' \
  -d '{"product_id":"PRD-004","birth_date":"1985-04-12","gender":"男性","sum_insured":3000000,"smoker_flag":true}'
```

停止:

```bash
docker compose down
```

---

## 3. OpenAPI 仕様の書き出し

各サービスの OpenAPI（`services/<service>/openapi.yaml`）を再生成します。
Konnect の API スペック登録や Dev Portal に利用できます。

```bash
python3 scripts/export_openapi.py
```

---

## 4. Kong Konnect の構築（Terraform）

Control Plane・Service・Route・Data Plane 証明書をすべて Terraform で構築します
（現状プラグインなし）。

```bash
cd terraform

# PAT は環境変数で渡す(tfvars には書かない)
export TF_VAR_konnect_pat=<Konnect Personal Access Token>

terraform init
terraform plan     # 事前確認
terraform apply    # 反映
```

`terraform apply` で以下が作成されます:

- Control Plane `kong-insurance-demo`
- 6つの Service と Route（`/product` 〜 `/claim`）
- Kong Data Plane 接続用の自己署名証明書（`certs/tls.crt` / `tls.key` に出力し、Konnect に登録）

> リージョンが us 以外の場合は変数 `konnect_server_url` を `https://eu.api.konghq.com` などに
> 変更します（`terraform.tfvars` または `-var` で指定）。
> `terraform.tfvars.example` をコピーして `terraform.tfvars` を作成できます。

設定変更（Service/Route の追加・変更など）は `.tf` を編集して再度 `terraform apply` するだけです。
削除は `terraform destroy` で Control Plane ごと消えます。

---

## 5. Kong Gateway (Data Plane) の接続

Konnect の Control Plane に接続する Data Plane をローカルで起動し、プロキシ経由で
各サービスにアクセスします。

### 5-1. 接続情報を .env に設定

Terraform の出力から DP 起動用の接続情報を取得し、`.env` に記載します
（`.env.example` をコピーして編集）。証明書は手順4で `certs/` に生成済みです。

```bash
cd terraform
terraform output dp_env    # KONNECT_CP_ENDPOINT などが出力される
```

出力例を `.env` に貼り付けます:

```
KONNECT_CP_ENDPOINT=xxxxxxxxxx.us.cp.konghq.com:443
KONNECT_CP_SERVER_NAME=xxxxxxxxxx.us.cp.konghq.com
KONNECT_TP_ENDPOINT=xxxxxxxxxx.us.tp.konghq.com:443
KONNECT_TP_SERVER_NAME=xxxxxxxxxx.us.tp.konghq.com
```

### 5-2. DP の起動

```bash
docker compose --profile konnect up -d
```

プロキシ経由の確認:

```bash
curl http://localhost:8000/product/products
curl http://localhost:8000/customer/customers?limit=3
curl -X POST http://localhost:8000/simulation/simulations \
  -H 'content-type: application/json' \
  -d '{"product_id":"PRD-005","birth_date":"2022-01-01","sum_insured":500000}'
```

> ローカルの 8000/8443 が他プロセスで使用中の場合は、`docker-compose.override.yml` で
> ポートを変更できます（例: `8100:8000` / `8543:8443`）。

---

## 6. AWS ECS 対応（後工程）

後工程で追加予定。各 FastAPI サービスを ECS タスクとして稼働させ、Kong DP も ECS 上で
hybrid 接続する構成を想定しています。詳細は別途本節に追記します。

---

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| `docker compose up` でポート競合 | 既存プロセスが 8000〜8006 を使用中。`lsof -iTCP:<port>` で確認し、`docker-compose.override.yml` でポート変更 |
| terraform apply で認証エラー | 環境変数 `TF_VAR_konnect_pat` と、リージョン(`konnect_server_url`) を確認 |
| DP が Konnect に接続できない | `.env` の CP/TP エンドポイント(`terraform output dp_env`)と、`certs/` に証明書が生成済みか確認 |
| サービスが 500 を返す | `data/seed/*.json` が生成済みか確認（手順1）。コンテナ内では `SEED_FILE` を参照 |
