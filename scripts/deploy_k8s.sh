#!/usr/bin/env bash
# 保険ドメイン APIバンドルを Kubernetes(Minikube)にデプロイする。
#
# 前提:
#   - kubectl / minikube が利用可能で、対象クラスタに接続済み
#   - Kong Operator と Gateway API CRD が導入済み(scripts/setup_kong_operator.sh)
#   - terraform/konnect を apply 済み(Control Plane が存在する)
#   - 環境変数 KONNECT_PAT に Konnect の Personal Access Token
#
# 使い方: ./scripts/deploy_k8s.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
NS=insurance

: "${KONNECT_PAT:?環境変数 KONNECT_PAT を設定してください}"

echo "==> Control Plane ID を Terraform 出力から取得"
CP_ID="$(terraform -chdir=terraform/konnect output -raw control_plane_id)"
echo "    CP_ID=$CP_ID"

echo "==> namespace とバックエンド6サービスを適用"
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/services/services.yaml

echo "==> Konnect PAT の Secret を作成(ラベル konghq.com/secret=true が必須)"
kubectl -n "$NS" create secret generic konnect-pat \
  --from-literal=token="$KONNECT_PAT" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "$NS" label secret konnect-pat \
  konghq.com/secret=true konghq.com/credential=konnect --overwrite

echo "==> Konnect 接続(auth / mirror CP / extension)を適用"
sed "s/__CONTROL_PLANE_ID__/$CP_ID/" k8s/kong/konnect.yaml | kubectl apply -f -

echo "==> KonnectExtension が Ready になるまで待機"
kubectl -n "$NS" wait --for=condition=Ready konnectextension/insurance-konnect --timeout=180s

echo "==> Gateway と Route(KongService/KongRoute)を適用"
kubectl apply -f k8s/kong/gateway.yaml
kubectl apply -f k8s/kong/routes.yaml

echo "==> バックエンドの Deployment が利用可能になるまで待機"
kubectl -n "$NS" wait --for=condition=available deployment --all --timeout=180s

cat <<EOF

==> 完了。プロキシ経由の動作確認(別ターミナルで port-forward):
    SVC=\$(kubectl -n $NS get svc -o name | grep dataplane-ingress)
    kubectl -n $NS port-forward \$SVC 8080:80

    curl http://localhost:8080/product/products
    curl "http://localhost:8080/customer/customers?limit=3"
EOF
