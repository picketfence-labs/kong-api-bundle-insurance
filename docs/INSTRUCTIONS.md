# 環境構築手順（Kubernetes / Minikube）

6サービスと Kong Gateway (Data Plane) を Kubernetes 上で稼働させます。ゲートウェイは
**Kong Operator** が管理し、Service/Route は Kong Operator の CRD で定義します。
Control Plane は Terraform で作成し、ローカル検証には Minikube を使います。

```mermaid
flowchart LR
  s0["0. 前提ツール"] --> s1["1. テストデータ生成"]
  s1 --> s2["2. イメージビルド<br/>(Minikube)"]
  s2 --> s3["3. Kong Operator導入"]
  s3 --> s4["4. Konnect CP作成<br/>(Terraform)"]
  s4 --> s5["5. K8sデプロイ"]
  s5 --> s6["6. 動作確認"]
```

## 0. 前提ツール

| ツール | 用途 |
|---|---|
| Docker | イメージビルド |
| minikube | ローカル Kubernetes |
| kubectl | Kubernetes 操作 |
| helm v3 | Kong Operator 導入 |
| Terraform v1.5+ | Konnect Control Plane 作成 |
| Python 3.11+ | テストデータ生成・OpenAPI書き出し |
| Kong Konnect アカウント + PAT | Control Plane 連携 |

```bash
minikube start   # 例: minikube start --driver=docker --cpus=4 --memory=6144
```

## 1. テストデータの生成

```bash
python3 -m pip install -r scripts/requirements.txt
python3 scripts/generate_test_data.py
```

出力: `data/seed/{product,customer,application,policy,claim}.json`
（simulation は永続データを持たないためファイルなし）。イメージビルド時に同梱されます。

## 2. サービスイメージのビルド（Minikube）

Minikube の Docker デーモン内に直接ビルドし、レジストリ無しで参照できるようにします
（`imagePullPolicy: IfNotPresent`）。

```bash
./scripts/build_images_minikube.sh
```

`insurance-{product,customer,simulation,application,policy,claim}:local` が作成されます。

## 3. Kong Operator と Gateway API の導入（初回のみ）

```bash
./scripts/setup_kong_operator.sh
```

Gateway API CRD と Kong Operator（`kong/kong-operator` Helm チャート）を導入します。
導入済みの場合はスキップして構いません。

## 4. Konnect の Control Plane を作成（Terraform）

Control Plane のみを Terraform で作成します（Service/Route は手順5の CRD で管理）。

```bash
export TF_VAR_konnect_pat=<Konnect Personal Access Token>
terraform -chdir=terraform/konnect init
terraform -chdir=terraform/konnect apply
```

作成物: Control Plane `kong-insurance-demo`。ID は次で参照できます:

```bash
terraform -chdir=terraform/konnect output -raw control_plane_id
```

> リージョンが us 以外の場合は変数 `konnect_server_url` を変更します
> （`terraform.tfvars` または `-var`）。

## 5. Kubernetes へのデプロイ

```bash
export KONNECT_PAT=$TF_VAR_konnect_pat
./scripts/deploy_k8s.sh
```

`deploy_k8s.sh` は以下を行います:

1. `insurance` namespace と6サービス（Deployment/Service）を適用
2. Konnect PAT の Secret を作成（**ラベル `konghq.com/secret=true` が必須**）
3. Konnect 接続（`KonnectAPIAuthConfiguration` / Mirror の `KonnectGatewayControlPlane` / `KonnectExtension`）を適用。Control Plane ID は Terraform 出力から自動挿入
4. `KonnectExtension` が Ready になるまで待機（DP クライアント証明書は Operator が自動発行）
5. Gateway と Route（`KongService`/`KongRoute`）を適用

手動で行う場合の要点（`k8s/kong/konnect.yaml` 冒頭コメント参照）:

```bash
kubectl -n insurance create secret generic konnect-pat --from-literal=token=$KONNECT_PAT
kubectl -n insurance label secret konnect-pat konghq.com/secret=true konghq.com/credential=konnect
```

> **注意:** Secret に `konghq.com/secret=true` を付けないと、Kong Operator の Secret
> キャッシュが対象外とし `Secret not found` になります。

## 6. 動作確認

Kong DP のプロキシ Service に port-forward してアクセスします（Minikube では
LoadBalancer の EXTERNAL-IP は `minikube tunnel` 無しでは pending のままですが、
port-forward で確認できます）。

```bash
SVC=$(kubectl -n insurance get svc -o name | grep dataplane-ingress)
kubectl -n insurance port-forward "$SVC" 8080:80 &

curl http://localhost:8080/product/products
curl "http://localhost:8080/customer/customers?limit=3"
curl -X POST http://localhost:8080/simulation/simulations \
  -H 'content-type: application/json' \
  -d '{"product_id":"PRD-005","birth_date":"2022-01-01","sum_insured":500000}'
```

Konnect 上の Service/Route は次で確認できます:

```bash
kubectl -n insurance get kongservice,kongroute
```

## 補足: OpenAPI 仕様の書き出し

```bash
python3 scripts/export_openapi.py
```

各サービスの `services/<service>/openapi.yaml` を再生成します。

## 破棄

```bash
kubectl delete -f k8s/kong/routes.yaml -f k8s/kong/gateway.yaml
kubectl delete namespace insurance
terraform -chdir=terraform/konnect destroy   # Konnect Control Plane を削除
```

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| `KonnectAPIAuthConfiguration` が VALID=False（`Secret not found`） | PAT Secret に `konghq.com/secret=true` ラベルが付いているか確認 |
| `KonnectExtension` が Ready にならない | `terraform output control_plane_id` と `konnect.yaml` の CP ID 一致、PAT の権限を確認 |
| DataPlane が Ready にならない | ingress Service（LoadBalancer）が pending でも DP Pod 自体は稼働。port-forward で確認可 |
| ルートが 404 | `kubectl -n insurance get kongservice,kongroute` で PROGRAMMED=True か、`paths` を確認 |
| Pod が ImagePullBackOff | `./scripts/build_images_minikube.sh` を実行し、`eval $(minikube docker-env)` 環境でビルド済みか確認 |
| サービスが 500 | `data/seed/*.json` を生成済みか（手順1）。イメージに同梱される |
