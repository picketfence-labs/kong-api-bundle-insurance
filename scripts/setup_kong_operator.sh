#!/usr/bin/env bash
# Kong Operator と Gateway API CRD をクラスタに導入する(初回のみ)。
#
# 前提: kubectl / helm が対象クラスタに接続済み。
# 使い方: ./scripts/setup_kong_operator.sh
set -euo pipefail

GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.2.1}"

echo "==> Gateway API CRD を導入 (${GATEWAY_API_VERSION})"
kubectl apply -f "https://github.com/kubernetes-sigs/gateway-api/releases/download/${GATEWAY_API_VERSION}/standard-install.yaml"

echo "==> Kong Helm リポジトリを追加"
helm repo add kong https://charts.konghq.com >/dev/null 2>&1 || true
helm repo update kong

echo "==> Kong Operator を導入 (namespace: kong-system)"
helm upgrade --install kong-operator kong/kong-operator \
  --namespace kong-system --create-namespace \
  --wait

echo "==> 完了。導入された CRD の一部:"
kubectl get crd | grep -E "konnect|kongservice|kongroute|dataplane|gatewayconfiguration" || true
