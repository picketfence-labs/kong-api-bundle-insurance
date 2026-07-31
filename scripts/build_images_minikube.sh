#!/usr/bin/env bash
# 6サービスのコンテナイメージを Minikube の Docker デーモン内にビルドする。
# これにより imagePullPolicy: IfNotPresent でクラスタから参照できる(レジストリ不要)。
#
# 前提: minikube 起動済み、docker が利用可能。
# 使い方: ./scripts/build_images_minikube.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
SERVICES=(product customer simulation application policy claim)

echo "==> Minikube の Docker 環境に切り替え"
eval "$(minikube docker-env)"

for svc in "${SERVICES[@]}"; do
  echo "==> build insurance-${svc}:local"
  docker build -q -f services/Dockerfile --build-arg SERVICE="$svc" -t "insurance-${svc}:local" . >/dev/null
done

echo "==> 完了:"
docker images | grep "^insurance-" | awk '{print "   ", $1, $2}'
