# アーキテクチャ

## 全体構成

```
                 ┌─────────────────────────────┐
                 │        Kong Konnect          │
                 │  (Control Plane: kong-        │
                 │   insurance-demo / US region) │
                 │   Service / Route 定義を管理   │
                 └──────────────┬──────────────┘
                                │ 設定配信・テレメトリ (mTLS)
                                ▼
   Client ──▶ ┌──────────────────────────────┐
              │  Kong Gateway (Data Plane)     │  hybrid mode
              │  3.15 Enterprise               │  プロキシのみ(DBレス)
              └──────────────┬───────────────┘
                             │  /product /customer /simulation
                             │  /application /policy /claim
        ┌────────┬───────────┼───────────┬────────┬────────┐
        ▼        ▼           ▼           ▼        ▼        ▼
    product  customer  simulation  application  policy   claim   ← FastAPI (各コンテナ)
      :8000    :8000     :8000       :8000      :8000    :8000
        │        │          │(計算のみ)   │         │        │
        └── data/seed/*.json をメモリにロードしてCRUD ──────┘
```

- **Kong Konnect** が Control Plane。Service / Route の宣言的設定を decK で反映する。
- **Kong Gateway (Data Plane)** は hybrid mode で Konnect に接続し、設定を受け取ってプロキシに徹する（ローカルDBを持たない）。
- **6サービス** はいずれも FastAPI 製。ローカルでは同一 Docker ネットワーク内でサービス名解決され、DP からプロキシされる。

## 技術選定

| 項目 | 選定 | 理由 |
|---|---|---|
| 実装言語 | Python 3.13 / FastAPI | OpenAPI 3.1 を自動生成でき、Konnect へのスペック登録・decK 連携と相性が良い。CRUDデモの実装速度も速い |
| データ保持 | 起動時に JSON をメモリロード | デモ用途。DBを立てずに整合性の取れた固定データを提供でき、再起動でシードにリセットされる |
| Gateway | Kong Gateway Enterprise 3.15 (hybrid) | 要件。Konnect の Control Plane と接続する Data Plane として動作 |
| 宣言的管理 | decK | Service/Route をコードで管理し、Konnect に冪等に反映 |

## データモデルとサービス間整合性

- `product`(5) と `customer`(100) を基点に、`application`(300) がこれらを参照。
- 承認済み `application`(200件) が `policy`(200) に 1:1 で対応（`application_id` 必須）。
- `claim`(50) は有効な `policy` を参照し、請求種別は対象商品カテゴリと矛盾しない。
- `simulation` は永続データを持たず、`common.premium` の共通ロジックで `policy` の保険料と一貫した試算を返す。

詳細なフィールド定義・設計判断は [DATA.md](DATA.md) を参照。

## 共通モジュール (`common/`)

| モジュール | 役割 |
|---|---|
| `jp_data.py` | 日本フォーマット生成（郵便番号×都道府県×市区町村の実在組合せ、市外局番、マイナンバーのチェックデジット、銀行口座、氏名・カナ） |
| `products.py` | 商品マスタの単一情報源（product サービス・simulation・データ生成が共有） |
| `premium.py` | 保険料算出ロジック（simulation と契約保険料生成が共有し一貫性を担保） |
| `store.py` | JSONシードのメモリロード＋簡易CRUD（5つのCRUDサービスが共有） |

## サービス実装パターン

CRUD5サービス（product/customer/application/policy/claim）は同一構造:

- `common.store.JsonStore` でシードをロードし、`GET(list/detail)` `POST` `PUT` `DELETE` `GET /health` を提供
- Pydantic モデルでスキーマを定義（→ OpenAPI 3.1 に反映）
- 一覧は代表的な項目でのフィルタ＋`skip`/`limit` ページング

`simulation` のみ例外で、永続データを持たないステートレスな計算API（`POST /simulations`）。

## コンテナ構成

- 全サービスが単一の `services/Dockerfile` を共有し、ビルド引数 `SERVICE` で切り替える（ビルドコンテキストはリポジトリルート）。
- コンテナ内は `PYTHONPATH=/app`、`common/` と対象サービスの `app/`、`data/seed/` をコピー。
- シードファイルのパスは環境変数 `SEED_FILE` で指定（未指定時はリポジトリの `data/seed/<service>.json`）。

## ネットワーク / ポート

| 用途 | ローカルポート |
|---|---|
| product / customer / simulation / application / policy / claim | 8001〜8006 |
| Kong DP プロキシ (HTTP / HTTPS) | 8000 / 8443 |

DP は `--profile konnect` を付けたときのみ起動する（Konnect 接続情報が必要なため）。

## 今後の拡張

- **認証プラグイン**: 現状は Service/Route のみ。key-auth / OIDC / rate-limiting 等を decK に追加予定。
- **マイナンバーのマスキング**: 利用者ロールに応じた raw/masked 切り替え（現状は raw 返却）。
- **AWS ECS 対応**: 各サービスを ECS タスクとして稼働、DP も ECS 上で hybrid 接続する構成を後工程で追加。
