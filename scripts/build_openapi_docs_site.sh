#!/usr/bin/env bash
# 各サービスの services/<service>/openapi.yaml から、GitHub Pages 公開用の
# 静的サイトを生成する。ビルドツールは使わず、Scalar(@scalar/api-reference)を
# CDN経由で読み込む薄いHTMLシェルをサービスごとに配置する(ADR 0009。
# @scalar/cli には静的HTML生成コマンドが無いため採用した方式、
# 詳細は docs/troubleshooting-log.md の2026-09-05エントリを参照)。
#
# 使い方: ./scripts/build_openapi_docs_site.sh [出力先ディレクトリ(既定: _site)]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${1:-${ROOT}/_site}"
SCALAR_VERSION="1.67.0"
SERVICES=(product customer simulation application policy claim)

service_label() {
  case "$1" in
    product) echo "商品マスタ" ;;
    customer) echo "顧客" ;;
    simulation) echo "保険料試算" ;;
    application) echo "申込" ;;
    policy) echo "契約" ;;
    claim) echo "保険金請求" ;;
  esac
}

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}/api"

for service in "${SERVICES[@]}"; do
  echo "==> ${service} 用のDocページを生成"
  SERVICE_DIR="${OUT_DIR}/api/${service}"
  mkdir -p "${SERVICE_DIR}"
  cp "${ROOT}/services/${service}/openapi.yaml" "${SERVICE_DIR}/openapi.yaml"
  cat > "${SERVICE_DIR}/index.html" <<HTML
<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${service} API — Kong API Bundle（損害保険ドメイン）</title>
  </head>
  <body>
    <div id="app"></div>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference@${SCALAR_VERSION}"></script>
    <script>
      Scalar.createApiReference('#app', {
        url: './openapi.yaml',
      })
    </script>
  </body>
</html>
HTML
done

echo "==> ルートインデックスを生成"
{
  echo "<!doctype html>"
  echo "<html lang=\"ja\">"
  echo "  <head>"
  echo "    <meta charset=\"utf-8\" />"
  echo "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />"
  echo "    <title>Kong API Bundle — OpenAPI Docs</title>"
  echo "  </head>"
  echo "  <body>"
  echo "    <h1>Kong API Bundle — OpenAPI Docs（損害保険ドメイン）</h1>"
  echo "    <ul>"
  for service in "${SERVICES[@]}"; do
    echo "      <li><a href=\"./api/${service}/\">${service}</a> — $(service_label "${service}")</li>"
  done
  echo "    </ul>"
  echo "  </body>"
  echo "</html>"
} > "${OUT_DIR}/index.html"

echo "==> 完了: ${OUT_DIR}"
