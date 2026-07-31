#!/usr/bin/env bash
# Kong Data Plane を Konnect に接続するための証明書を生成し、Konnect に登録する。
#
# 前提:
#   - 環境変数 KONNECT_PAT に Konnect の Personal Access Token を設定済み
#   - openssl / curl / python3 が利用可能
#   - Control Plane 名は kong-insurance-demo(必要に応じて CP_NAME を変更)
#
# 実行後、deck/certs/tls.crt と deck/certs/tls.key が生成され、
# 証明書が Konnect の Control Plane に data-plane client cert として登録される。
# 続けて `docker compose --profile konnect up -d` で DP を起動できる。
set -euo pipefail

REGION="${KONNECT_REGION:-us}"
KONNECT_ADDR="https://${REGION}.api.konghq.com"
CP_NAME="${CP_NAME:-kong-insurance-demo}"
CERT_DIR="$(cd "$(dirname "$0")/.." && pwd)/deck/certs"

: "${KONNECT_PAT:?環境変数 KONNECT_PAT を設定してください}"

mkdir -p "$CERT_DIR"

echo "==> Control Plane ID を取得中 ($CP_NAME @ $REGION)"
CP_ID=$(curl -s "$KONNECT_ADDR/v2/control-planes?page%5Bsize%5D=100" \
  -H "Authorization: Bearer $KONNECT_PAT" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(next((x['id'] for x in d['data'] if x['name']=='$CP_NAME'),''))")

if [ -z "$CP_ID" ]; then
  echo "エラー: Control Plane '$CP_NAME' が見つかりません" >&2
  exit 1
fi
echo "    CP_ID=$CP_ID"

echo "==> Data Plane 用の証明書ペアを生成中"
openssl req -new -x509 -nodes -newkey rsa:2048 \
  -subj "/CN=kong-insurance-dp/C=JP" \
  -keyout "$CERT_DIR/tls.key" \
  -out "$CERT_DIR/tls.crt" \
  -days 1095 2>/dev/null
echo "    $CERT_DIR/tls.crt"
echo "    $CERT_DIR/tls.key"

echo "==> 証明書を Konnect に登録中"
CERT_PAYLOAD=$(python3 -c "import json,sys;print(json.dumps({'cert':open('$CERT_DIR/tls.crt').read()}))")
curl -s -X POST "$KONNECT_ADDR/v2/control-planes/$CP_ID/dp-client-certificates" \
  -H "Authorization: Bearer $KONNECT_PAT" \
  -H "Content-Type: application/json" \
  -d "$CERT_PAYLOAD" | python3 -c "import sys,json;d=json.load(sys.stdin);print('    registered cert id:',d.get('item',{}).get('id','(既存の可能性)'))" || true

echo "==> .env に書き込む接続情報"
CP_ENDPOINT=$(curl -s "$KONNECT_ADDR/v2/control-planes/$CP_ID" -H "Authorization: Bearer $KONNECT_PAT" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['config']['control_plane_endpoint'])")
TP_ENDPOINT=$(curl -s "$KONNECT_ADDR/v2/control-planes/$CP_ID" -H "Authorization: Bearer $KONNECT_PAT" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['config']['telemetry_endpoint'])")
CP_HOST=${CP_ENDPOINT#https://}
TP_HOST=${TP_ENDPOINT#https://}

cat <<EOF

以下を .env に記載してください(scripts/setup_konnect_dp.sh が出力):

KONNECT_CP_ENDPOINT=${CP_HOST}:443
KONNECT_CP_SERVER_NAME=${CP_HOST}
KONNECT_TP_ENDPOINT=${TP_HOST}:443
KONNECT_TP_SERVER_NAME=${TP_HOST}

続いて:  docker compose --profile konnect up -d
EOF
