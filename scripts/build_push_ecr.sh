#!/usr/bin/env bash
# 6サービスのコンテナイメージをビルドし、ECR に push する。
#
# 前提:
#   - AWS 認証情報が設定済み(aws sts get-caller-identity が通ること)
#   - terraform/ecs を apply 済み(ECRリポジトリが作成済み)
#   - Docker が利用可能
#
# 使い方:
#   ./scripts/build_push_ecr.sh [IMAGE_TAG]
#   (IMAGE_TAG 省略時は latest)
set -euo pipefail

IMAGE_TAG="${1:-latest}"
AWS_REGION="${AWS_REGION:-$(aws configure get region)}"
PROJECT="${PROJECT_NAME:-kong-insurance}"
SERVICES=(product customer simulation application policy claim)

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "==> ECR ログイン ($REGISTRY)"
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

# ECR は linux/amd64 で動作するため、明示的に amd64 でビルドする。
PLATFORM="linux/amd64"

for svc in "${SERVICES[@]}"; do
  repo="${PROJECT}/${svc}"
  image="${REGISTRY}/${repo}:${IMAGE_TAG}"
  echo "==> build & push: ${svc} -> ${image}"
  docker build \
    --platform "$PLATFORM" \
    -f services/Dockerfile \
    --build-arg SERVICE="$svc" \
    -t "$image" .
  docker push "$image"
done

echo "==> 完了。ECS サービスを更新して新イメージを反映する場合:"
echo "    aws ecs update-service --cluster ${PROJECT} --service <service> --force-new-deployment --region ${AWS_REGION}"
