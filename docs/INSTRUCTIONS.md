# 環境構築手順

## 0. 前提ツール

- Docker / Docker Compose v2
- Python 3.11+（テストデータ生成・OpenAPI書き出し用。3.13 で確認済み）
- [decK](https://docs.konghq.com/deck/) v1.53+（Konnect 連携）
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

## 4. Kong Konnect への反映（decK）

Service / Route の宣言的設定を Konnect に反映します（現状プラグインなし）。

```bash
export KONNECT_PAT=<Konnect Personal Access Token>

# 事前確認(差分表示)
deck gateway diff deck/kong.yaml \
  --konnect-token "$KONNECT_PAT" \
  --konnect-addr https://us.api.konghq.com \
  --konnect-control-plane-name kong-insurance-demo

# 反映
deck gateway sync deck/kong.yaml \
  --konnect-token "$KONNECT_PAT" \
  --konnect-addr https://us.api.konghq.com \
  --konnect-control-plane-name kong-insurance-demo
```

> リージョンが us 以外の場合は `--konnect-addr` を `https://eu.api.konghq.com` などに変更します。
> Control Plane が未作成の場合は Konnect UI か API で作成してください（本デモでは `kong-insurance-demo` を使用）。

---

## 5. Kong Gateway (Data Plane) の接続

Konnect の Control Plane に接続する Data Plane をローカルで起動し、プロキシ経由で
各サービスにアクセスします。

### 5-1. DP 証明書の生成と登録

```bash
export KONNECT_PAT=<Konnect Personal Access Token>
./scripts/setup_konnect_dp.sh
```

このスクリプトは以下を行います:

1. `deck/certs/tls.crt` / `tls.key` を生成（`deck/certs/` は .gitignore 済み）
2. 証明書を Konnect の Control Plane に data-plane client cert として登録
3. `.env` に記載すべき接続情報（CP/TP エンドポイント）を出力

出力された値を `.env` に記載します（`.env.example` をコピーして編集）。

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
| decK sync で `control plane not found` | `--konnect-control-plane-name` と `--konnect-addr`(リージョン) を確認 |
| DP が Konnect に接続できない | `.env` の CP/TP エンドポイントと、証明書が Konnect に登録済みか確認（`scripts/setup_konnect_dp.sh` を再実行） |
| サービスが 500 を返す | `data/seed/*.json` が生成済みか確認（手順1）。コンテナ内では `SEED_FILE` を参照 |
