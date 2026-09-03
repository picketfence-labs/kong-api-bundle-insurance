# CLAUDE.md — 本リポジトリでの取り決め

このファイルは、本リポジトリで作業する際の方針・取り決めをまとめたものです。

## プロジェクトの目的

Kong Gateway Enterprise 3.15 + Kong Konnect を前段に置き、損害保険ドメインの
6サンプルAPI（product / simulation / customer / application / policy / claim）を
稼働させるデモ環境。**このリポジトリは公開予定**。実行基盤は Kubernetes（ローカル検証は Minikube）、ゲートウェイは Kong Operator で管理する。

## ドキュメント構成の取り決め

| ファイル | 役割 |
|---|---|
| `README.md` | リポジトリのREADME。プロジェクト概要と利用方法（ルート直下） |
| `CLAUDE.md` | 本ファイル。指示・取り決めのまとめ（ルート直下） |
| `CHANGELOG.md` | バージョンごとの変更履歴（ルート直下）。OSSエコシステムの慣習上ルート直下が期待されるための例外（`git tag`のみを正とし、`main`マージ時にGitHub Actionsが自動追記。詳細: [ADR 0002](docs/decisions/0002-changelog-method.md)/[ADR 0005](docs/decisions/0005-changelog-commit-mechanism.md)） |
| `docs/DATA.md` | データモデル定義と設計判断の記録 |
| `docs/ARCHITECTURE.md` | 全体構成・技術的な説明 |
| `docs/INSTRUCTIONS.md` | 環境の構築手順 |
| `docs/design-brief.md` | コンテナ化・パブリックレジストリ公開の基本設計（Dev Design Brief） |
| `docs/decisions/NNNN-*.md` | 複数の妥当な選択肢がある判断ポイントの記録（ADR）。1判断＝1ファイル |
| `docs/troubleshooting-log.md` | 実装中に想定通りに動かなかったこと（エラー・仕様の相違・プロセスの摩擦等）を漏れなく記録するログ。判断ポイントかどうかに関わらず、その場で追記する |

- `README.md`・`CLAUDE.md`・`CHANGELOG.md`（OSSエコシステムの慣習上の例外）**以外**のドキュメントは `docs/` 配下に置く。
- **ダイアグラムはすべて mermaid 形式で記述する**（```` ```mermaid ````）。ASCIIアートは使わない。GitHub・claude.ai のどちらでもレンダリングされる構文を用いる。

## 設計・実装の方針

- **言語/FW**: 全サービス Python / FastAPI で統一。
- **データ**: すべて日本語。日本のフォーマット（郵便番号・都道府県・電話番号・マイナンバー等）に準拠。
  マイナンバーは総務省告示のチェックデジット算出方法に準拠したダミー値。
- **テストデータ**: 全サービスをまたいで参照整合性を担保する（`scripts/generate_test_data.py` で一括生成）。
  商品カテゴリと請求種別の整合など、ドメイン的な矛盾を作らない。
- **商品ドメイン**: 損害保険会社を想定。生命保険・学資保険は扱わない。
- **マイナンバーのAPI公開**: 現状は raw（フル桁）で返却。将来、利用者ロールに応じて raw/masked を切り替える。
- **実行基盤**: Kubernetes に一本化（Docker Compose・AWS ECS は廃止）。ローカル検証は Minikube。サービスイメージは GHCR（`ghcr.io/picketfence-labs/insurance-<service>`）から `imagePullPolicy: IfNotPresent` でpullする（`scripts/deploy_k8s.sh`が`IMAGE_TAG`環境変数でタグを解決、既定`v0.1.0`。詳細: [ADR 0007](docs/decisions/0007-minikube-deploy-image-source.md)）。未pushのローカルコード変更を試す場合のみ`scripts/build_images_minikube.sh` + `IMAGE_TAG=local`のローカルビルド経路を使う。
- **コンテナ公開・バージョニング方針**: 6サービスのイメージはパブリックレジストリ（GHCR、`ghcr.io/picketfence-labs/insurance-<service>`）へ公開する。バージョンはリポジトリ全体で一括管理し（`git tag`のみを正とし、`VERSION`ファイルは持たない）、`main` マージ時に GitHub Actions が自動でパッチバージョンを算出・build・push・GitHub Release 作成（Change Log登録）まで行う。`CHANGELOG.md` の更新は bot が自動作成した PR をその場で auto-merge する方式で `main` へ反映する（branch protection 下でも直接 push を発生させないため）。詳細・判断根拠は [docs/design-brief.md](docs/design-brief.md) と対応する ADR（[0001](docs/decisions/0001-versioning-granularity.md) 〜 [0005](docs/decisions/0005-changelog-commit-mechanism.md)）を参照。**この節と設計ブリーフの内容が食い違った場合は設計ブリーフ側を正とし、この節を追従修正する**。
- **ゲートウェイ管理**: **Kong Operator** を使用（decK は使用しない）。Service/Route は Kong Operator の CRD（`KongService`/`KongRoute`）で定義し、Konnect に同期する。認証等のプラグインは後日 `KongPlugin` CRD で追加。
- **Konnect / IaC の役割分担**: Control Plane は **Terraform**（`terraform/konnect/`）が作成・所有し、k8s の `KonnectGatewayControlPlane` は `source: Mirror` で ID 参照するのみ。DP クライアント証明書は `KonnectExtension`（provisioning: Automatic）で Operator が自動発行するため Terraform では扱わない。
- **PAT Secret のラベル**: Kong Operator の Secret キャッシュはラベル `konghq.com/secret=true` で絞り込む。PAT Secret にこのラベルが無いと `Secret not found` になるため必須。
- **Konnect 反映先**: US リージョン / 組織 `hashi-sandbox` / Control Plane `kong-insurance-demo`。

## データモデル変更のワークフロー

データモデルはユーザーが実施前に確認する。ドラフトを提示し、修正指示を受けてから実装に進む。
変更は `docs/DATA.md` に反映し、確定後に `scripts/generate_test_data.py` と各サービスのモデルを更新する。

## 開発ワークフロー（ブランチ・PR）

- **`main`への直接pushは禁止**。featureブランチを作成し、PRを経由してmergeする（`git checkout -b <branch>` → 実装・検証 → `git push -u origin <branch>` → `gh pr create` → レビュー後 `gh pr merge --squash --delete-branch`）。
- PR descriptionには最低限、**何を（What）・なぜ（Why）・どう検証したか（Testing）**の3点を含める。
- **PRの粒度は1PR=1テーマ**。「ついでに直した」を混ぜない。
- コミットメッセージの規約は特に定めない（本リポジトリの既存コミット履歴のスタイルに合わせる）。
- 検証がその場では完了できない変更（依存する環境が未整備等）をpushする場合、PRタイトルに `[WIP]` を付けるか `gh pr create --draft` で作成し、何が未検証かをPR descriptionに明記する。
- `main`マージ時に自動実行されるコンテナpush（上記「コンテナ公開・バージョニング方針」）があるため、**`main`へのPRレビューは通常以上に注意する**（マージ＝パブリックイメージの即時公開に直結する）。

## エスカレーション条件・完了報告フォーマット

以下に該当する場合は、自己判断で進めず、作業を止めて確認を取る:
1. 不可逆・破壊的な操作（保護ブランチへのforce push、公開後のGHCRタグ削除等）
2. 継続的にコストが発生する操作（本リポジトリの範囲では現時点で想定される操作は無いが、新たに発生した場合は該当）
3. 要件の曖昧さが実装の細部ではなく設計の方向性に影響する場合（複数の妥当な選択肢がある判断ポイントに遭遇した場合は、実装を進める前に選択肢と判断基準を提示し確認を取る。ADRの「検討した選択肢」「決定」「判断基準・根拠」は決定前に埋める）
4. 依頼されたタスクの範囲を超える作業が必要だと判明した場合（スコープ逸脱）
5. 機密情報の扱いに確信が持てない場合

読み取り専用の調査・既存パターンに従う追加的な変更・lint的な定型作業は、確認を挟まず進めてよい（人間の事後レビュー＝通常のPRフローは維持する）。

**タスク完了時の報告フォーマット**:
1. 何を実施したか（サマリ）
2. どう検証したか（テスト結果・実行ログ等。「動くはず」ではなく実際に確認した事実を書く）
3. 指示から逸脱した判断とその理由（あれば）
4. 未解決・持ち越しの論点
5. **CLAUDE.md・権限設定・連携ドキュメント自体に感じた摩擦・改善提案**（無ければ「特になし」と明記。**「特になし」であってもPR本文か`docs/troubleshooting-log.md`のいずれかに必ず書く**）

想定通りに動かなかったこと（エラー・ドキュメントとの相違・プロセスの摩擦等）は、判断ポイントかどうかに関わらず**その場で** `docs/troubleshooting-log.md` に追記する（後からまとめて思い出さない）。完了報告のタイミングで、このログの新規追加分を要約して報告に含める。

## テスト方針

- 現時点で自動テストは無い（新規ロジック追加時は対応するテストを書くことが望ましいが、既存コードへの大規模な後付けは必須ではない）
- コンテナ化・CIパイプラインについては、`terraform -chdir=terraform/konnect validate`・`docker build`のローカル成功に加え、実際にGitHub Actions上でbuild・push・Release作成が通ることを確認する（「動くはず」で済ませない）
- 可能な範囲でGitHub ActionsにCI（lint/build確認）を組み込む

## 秘匿情報の取り扱い

- `KONNECT_PAT` などのトークンは環境変数で渡す。**リポジトリにコミットしない**。
- `terraform.tfvars`、`*.tfstate` は `.gitignore` 済み。`terraform.tfvars.example` のみコミットする。
- Terraform の PAT は `TF_VAR_konnect_pat` 環境変数で渡す（tfvars に書かない）。
- Kubernetes の PAT は `konnect-pat` Secret として `kubectl` で作成する（マニフェストに平文で書かない）。`scripts/deploy_k8s.sh` が `KONNECT_PAT` 環境変数から作成する。
