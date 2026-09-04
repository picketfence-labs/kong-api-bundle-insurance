#!/usr/bin/env bash
# [開発用・任意] 未pushのローカルコード変更を Minikube 上で試すためのスクリプト。
# 標準のデプロイ経路は GHCR からのpull(scripts/deploy_k8s.sh, ADR 0007)であり、
# 本スクリプトは通常のデプロイでは不要。ローカル変更を確認したい場合のみ、
# 本スクリプトでビルド後に IMAGE_TAG=local ./scripts/deploy_k8s.sh を実行する
# (imagePullPolicy: IfNotPresent のため、同名タグがMinikubeのDockerに存在すれば
# pullを試みずそのまま使われる)。
#
# 前提: minikube 起動済み、docker が利用可能。
# 使い方: ./scripts/build_images_minikube.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
SERVICES=(product customer simulation application policy claim)
NAMESPACE=ghcr.io/picketfence-labs

echo "==> Minikube の Docker 環境に切り替え"
eval "$(minikube docker-env)"

for svc in "${SERVICES[@]}"; do
  echo "==> build ${NAMESPACE}/insurance-${svc}:local"
  docker build -q -f services/Dockerfile --build-arg SERVICE="$svc" \
    -t "${NAMESPACE}/insurance-${svc}:local" . >/dev/null
done

echo "==> 完了:"
docker images | grep "insurance-" | awk '{print "   ", $1, $2}'
