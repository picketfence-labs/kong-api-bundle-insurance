# Dev Design Brief — コンテナ説明改善（README再構成 + OpenAPI Doc公開）

Picketfence Labs Vault（Obsidianの管理ノート）の `Dev Design Brief Template` に沿って作成。本ドキュメントは、GHCR公開済み6コンテナ（insurance-product / customer / policy / simulation / claim / application）の「見え方」を改善するための基本設計。着手前にVault側で調査・確定した内容をここに転記している。`docs/design-brief.md`（コンテナ化・パブリックレジストリ公開の基本設計）の後続タスクにあたる。

> **ステータス**: 本ドキュメントは実装前の基本設計（Vault側での調査・方針決定まで完了）。README本文の実装、GitHub Actionsワークフローの実装は、このリポジトリを担当する開発セッションが行う。

## 1. Projectゴール
GHCR公開済み6コンテナについて、(a) パッケージページに表示される `README.md` 冒頭を「汎用デモAPIコンテナ」の趣旨に沿った内容へ再構成し、(b) 各サービスのOpenAPI Spec（`services/<service>/openapi.yaml`、既存）をGitHub Pages上で閲覧可能な形で公開できる状態にする。

## 2. 要件

### 現在（今回のスコープ）
- `README.md` 冒頭を、コンテナ利用者向けの説明（6つの汎用デモAPIコンテナを公開しているリポジトリである旨。6コンテナ共通内容でよい）に差し替える
- 既存のKong Gateway + Konnect + Kubernetesによるフルデモ環境の構築手順は、詳細を書き下すのではなく概要1〜2行＋リンクに圧縮する形で再配置する（例:「Kong Gatewayを使ったKubernetes環境での構築サンプルはこちら」。詳細自体は削除せず、同一README内の後方セクションとして残し、そこへのリンクとする）
- 各 `services/<service>/openapi.yaml` をOSSレンダラー（Scalar）で静的HTML化し、GitHub Pagesで公開する。既存のリリースCI（`main`マージ時にバージョン自動インクリメント→6イメージbuild→GHCRへpush→GitHub Release作成、詳細は `docs/design-brief.md` 参照）に統合されたステップとして実行する想定
- `README.md` の共通部分に、各サービスのGitHub Pages URL一覧を掲載する

### 将来（今回はやらないが、設計上ぶつからないようにする）
- サービス毎の独立バージョニングへの移行可能性（`docs/design-brief.md` より継承済みの将来要件。今回のREADME・Pages公開設計もこれと衝突しないようにする）
- 6サービス以外のコンテナが将来追加される可能性（README・GitHub Pages公開の構成はサービス追加に対して拡張しやすい形にしておく）
- ドキュメントの多言語化（今回は日本語のみ。将来英語版が必要になる可能性を設計上排除しない）

## 3. アーキテクチャ

**README再構成方針**: 現状の冒頭（プロジェクト全体紹介）を、コンテナ利用者向けの説明に差し替える。フルデモ環境（Kong Gateway + Konnect + Kubernetes）の構築手順は、既存の記述を削除せずそのまま後方セクションとして残しつつ、冒頭からは概要1〜2行＋アンカーリンクのみで参照する形にする（詳細を消さない、順序と要約粒度を変える再構成）。

**OpenAPI Doc公開パイプライン**: 各サービスの `services/<service>/openapi.yaml` をOSSレンダラー Scalar（セルフホスト用のOSSコンポーネント。SaaS版のScalar Registryとは別物）で静的HTML化し、GitHub Pagesとして公開する。出力パス構成（例: `docs/api/<service>/index.html` 案）・既存リリースワークフローへの統合方法（既存の `release` ワークフローにステップ追加するか、専用ワークフローとして分離するか）は実装時に確定する。

**判断の経緯（Vault側での事前調査、詳細は [ADR 0009](decisions/0009-openapi-doc-hosting.md)）**:
- GHCRパッケージページは、リンクされたリポジトリの `README.md` をそのまま表示するだけで、パッケージ個別の説明欄・添付ファイル欄は存在しない（実機での動作確認済み）。そのため「共通の `README.md` をどう再構成するか」以外の手段は無い
- OpenAPI提示方法として、(1) 公開Swagger UI（`petstore.swagger.io` 等の `?url=` パラメータ利用）、(2) Scalar/Bump.sh/Postman Public Workspace等の外部APIカタログSaaS、(3) GitHub Pages自前ホスト、の3方向を比較検討した
- SwaggerHub（現API Hub）・Stoplightはいずれも2023年8月にSmartBearへ買収済みであり同一ベンダー系列となるため除外。Scalarの無料ホスト枠はAPI登録数上限が3件で6サービスをカバーできない。Bump.sh・Postman Public Workspaceにも無料枠の制約・運用上のトレードオフがある
- 結果、追加の外部ベンダー依存を持たず6サービス全てを無料枠の制約なくカバーできる「GitHub Pages自前ホスト」を採用。静的HTML生成にはOSSレンダラーのScalarを用いる（ホスト型SaaSではなく、セルフホスト用コンポーネントとしての利用）

## 4. 技術スタック
- 既存: Python/FastAPI、Docker、GitHub Actions（バージョン自動更新・build・push・Release作成。詳細は `docs/design-brief.md` 参照）
- 追加予定: Scalar（OSSレンダラー、静的HTML生成用CLI）、GitHub Pages

## 5. 検証方法（テストケース）
- GHCRの6パッケージページ全てで、新しい `README.md` 冒頭（コンテナ向け説明）が表示されることを確認する（6パッケージとも同一 `README.md` を参照するため、1箇所の変更で全て反映されるはず）
- 各サービスのGitHub Pages URLが実際にScalarでレンダリングされ、対応するAPIエンドポイント・日本語説明が正しく表示されることを確認する
- `main` マージ後、既存のリリースCIに統合したPages公開ステップが自動実行され、バージョン更新と同じタイミングでPagesの内容も更新されることを確認する
- **外部依存の前提条件確認（着手前）**: GitHub Pagesはpublicリポジトリであれば無料プランでも有効化できる一般的な仕様だが、本リポジトリのOrganization設定で過去にGHCR関連の制約（[ADR 0006](decisions/0006-package-visibility-automation.md) / [ADR 0007](decisions/0007-package-visibility-manual-only.md)）が発覚した実績があるため、Pages機能自体が制限されていないかを実装着手前に確認する（思い込みで「今回も問題ない」と判断しない）

## 6. 成果物
- `README.md` 冒頭の再構成（コンテナ向け説明＋フルデモ環境への概要＋リンク）
- 各サービスのOpenAPI Spec静的HTML生成・GitHub Pages公開（6サービス分）
- 既存リリースCIへのPages公開ステップ統合（または専用ワークフロー追加）
- ADR 0009（本ブリーフの判断ポイントに対応。作成済み）

## 7. 関連する既存知見・参照先の棚卸し
- **(a) 既存Area/Resource**: Picketfence Labs Vault側で、GHCRコンテナパッケージの表示仕様（パッケージページはリンクリポジトリの `README.md` をそのまま表示し、個別説明欄を持たない）を検証した知見が今回新たに得られている。今後Vault側の `03-Resources` に蒸留予定
- **(b) ローカル参照**: 特になし（本タスクは本リポジトリ内で完結する）

## 関連
- `docs/design-brief.md` — 本タスクの前段（コンテナ化・パブリックレジストリ公開の基本設計）
- `CLAUDE.md` — 本リポジトリでの取り決め
- [ADR 0009](decisions/0009-openapi-doc-hosting.md) — 本ブリーフの判断ポイントに対応するADR
- `docs/troubleshooting-log.md` — 実装中の想定外・知見ログ
