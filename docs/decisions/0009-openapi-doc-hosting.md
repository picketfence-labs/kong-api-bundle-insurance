# ADR 0009: OpenAPI Doc公開方式の選定

- **日付**: 2026-09-05
- **状態**: 決定

## コンテキスト
各サービス（`services/<service>/openapi.yaml`）は既存だが、外部の閲覧者（他デモから本コンテナを利用する開発者等）が仕様をブラウザで確認できる形では公開されていない。GHCRパッケージページはリンクされたリポジトリの`README.md`をそのまま表示するのみで、パッケージ固有の説明欄・添付ファイル欄は存在しない（実機検証済み）ため、`README.md`にリンクを載せるだけでなく、実際にAPI仕様を閲覧できる手段を用意したい。

## 検討した選択肢
1. **公開Swagger UI（`petstore.swagger.io`等）への`?url=`パラメータでのリンク**: 追加インフラ不要。`raw.githubusercontent.com`のCORS許可（`access-control-allow-origin: *`）と実際のレンダリング成功を確認済み。ただしSmartBear運営の公開デモインスタンスを想定外の用途で利用する形になり、SLA無し・将来の提供停止リスクがある
2. **Scalar / Bump.sh / Postman Public Workspace等の外部APIカタログSaaS**: Scalarは無料ホスト枠（Registry）があるがAPI登録数上限が3件で6サービス全てをカバーできない。Bump.shは1ユーザー利用なら無料だがAPI登録数上限は未確認。Postman Public Workspaceは完全無料・件数上限なしだが、OpenAPIファイルの取り込みを都度同期する運用が必要になり、`postman.com`ドメインでの公開になりGitHubから離れる
3. **SwaggerHub（現API Hub）・Stoplightのホスト型サービス**: いずれも2023年8月にSmartBearへ買収済みであり、選択肢1と同一ベンダー系列に該当する。選択肢1を避ける動機（特定ベンダーへの依存回避）と同じ理由でこちらも除外
4. **GitHub Pages自前ホスト（OSSレンダラーで静的HTML生成）**: 追加のベンダー依存が発生せず、6サービス全てを無料枠の制約なくカバーできる。既存のリリースCI（バージョン自動インクリメント→6イメージbuild→GHCR push→Release作成）に1ステップ追加するだけで統合できる見込み。Redoc / Scalar / Stoplight Elementsいずれも自前ホスト用のOSSコンポーネントとして利用可能（Stoplight ElementsはSmartBear買収と無関係にOSSとして自前ホスト可能）

## 決定
選択肢4（GitHub Pages自前ホスト）を採用する。静的HTML生成に用いるOSSレンダラーはScalarとする。

## 判断基準・根拠
- 6サービス全てをカバーする必要があり、外部SaaSの無料枠上限（Scalar: 3件）に収まらない
- 特定ベンダー（SmartBear系列）への依存を避けたいという利用者の要件があり、選択肢1・3はいずれも同一ベンダー系列に該当するため不適
- 既存のリリースCIパイプラインへの追加ステップとして統合でき、実装コストが小さい（既製のMarketplace Action〈ReDocでの静的HTML生成→GitHub Pagesデプロイ〉も存在し、ゼロから構築する必要がない）
- レンダラーとしてScalarを選んだのは、Redoc/Stoplight Elementsと比較してより新しい見た目・組み込みAPIクライアントを備える点が決め手（利用者確認済み）

## 想定していたこと vs 実際どうだったか
- **想定**: `@scalar/cli`に、`openapi.yaml`から自己完結型の静的HTMLファイルを生成するCLIコマンドがある
- **実際**: `@scalar/cli`の`document serve`はローカル開発用のプレビューサーバーを起動するのみで、静的HTMLファイルを出力するコマンドは存在しない（DeepWiki `scalar/scalar`で確認、詳細は[troubleshooting-log.md](../troubleshooting-log.md)の2026-09-05エントリ）。代わりに、Scalarが公式に推奨する自前ホスト方式（`@scalar/api-reference`をCDN経由で読み込み`Scalar.createApiReference('#app', { url: './openapi.yaml' })`で初期化する数行のHTMLファイルを配置。ビルド不要）を採用した。「GitHub Pages自前ホスト + Scalar」という決定自体は変更なし、実現手段が「CLIでの静的HTML生成」から「CDN読み込み型HTMLシェルの配置」に変わった

## 影響・トレードオフ
- GitHub Pagesの公開設定（Organization/リポジトリ設定でPages機能自体が制限されていないか）を実装着手前に確認する必要がある（過去に本リポジトリのOrganization設定でGHCR関連の制約が発覚した実績〈ADR 0006/0007〉があるため、思い込みで判断しない）
- 将来6サービス以外のコンテナが追加された場合も、GitHub Pagesの出力パス構成（サービスごとのサブパス）はそのまま拡張できる設計にしておく必要がある
- CDN経由で読み込む`@scalar/api-reference`はバージョン固定なしだと将来の破壊的変更の影響を受ける（実装時にCDN URLへバージョンを固定指定する）

## 関連する決定
- [ADR 0004: コンテナレジストリの選定](0004-container-registry-choice.md)（公開レジストリ＝GHCR一本化の既定方針を、今回のドキュメント公開方針でも踏襲する形）
- `docs/design-brief-container-docs.md`（本ADRに対応する基本設計）
