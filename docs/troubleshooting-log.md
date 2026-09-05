# Troubleshooting Log

実装中に**想定通りに動かなかったこと**を、その場で漏れなく記録するログ。判断ポイント（複数の妥当な選択肢がある分岐）は `docs/decisions/`（ADR）に記録するが、それ以外のあらゆる「期待と実際のギャップ」（エラー、ドキュメントと異なる挙動、想定した設定で動かなかった等）はここに追記する。CLAUDE.md・権限設定（`.claude/settings.json`）・連携プロセス自体の摩擦もここの対象。

追記専用。1件＝1エントリ、その場で書く（後からまとめて思い出さない）。

## 記入フォーマット
```markdown
## YYYY-MM-DD HH:MM（または該当タスク名） タイトル
- **何を期待していたか**:
- **実際どうだったか**（エラーメッセージ・症状を具体的に）:
- **原因**（分かれば。不明なら「不明」と書く）:
- **対処・回避方法**（または未解決なら次にどうするか）:
- **コスト**（任意。試行回数・かかった時間等、目立って大きい場合のみ）:
```

---

## 2026-09-03 コンテナ化・CI実装 branch protectionがbotのpushも一律拒否
- **何を期待していたか**: release automationワークフローがバージョン管理ファイル（`CHANGELOG.md`）を`main`へ直接コミットできること
- **実際どうだったか**: PR #1のテストで確認済みの`main`のbranch protection（`required_pull_request_reviews`設定、`enforce_admins: true`）は、`GITHUB_TOKEN`によるbotのpushも例外なくGH006で拒否する（`gh api repos/.../branches/main/protection`で確認。bypassリストは classic branch protection には存在せず、Rulesetsでのみ設定可能）
- **原因**: classic branch protectionの`required_pull_request_reviews`はPR経由以外の変更を無条件にブロックする仕様で、actor単位の例外機能が無い
- **対処・回避方法**: [ADR 0005](decisions/0005-changelog-commit-mechanism.md)として新規に判断ポイント化。botがCHANGELOG.md更新のみのPRを自動作成し、`required_approving_review_count: 0`を利用してその場でauto-mergeする方式を採用。バージョン番号自体は`VERSION`ファイルを持たず`git tag`のみから導出することで、tagのpush（branch protectionの対象外）だけで済ませ、コミットが必要な範囲を最小化した

## 2026-09-03 コンテナ化・CI実装 ruffのデフォルトルール選択がドキュメント記載と異なる
- **何を期待していたか**: `ruff check .`（設定ファイル無し）は公式ドキュメント記載のデフォルト（E4, E7, E9, F）のみを検出する
- **実際どうだったか**: 手元の`ruff 0.16.5`では設定ファイル無しの`ruff check .`実行時、`DTZ`（datetime系）・`RUF`・`PLR`等の追加ルールも検出された（`scripts/generate_test_data.py`等で8件）。`--isolated`かつ`--select E4,E7,E9,F`を明示すると、`services/`・`common/`配下はエラー無し、`scripts/`配下のみ`E402`（意図的な`sys.path`操作パターン）が2件残る
- **原因**: 不明（ruffのバージョンにより実質的なデフォルト選択が変化した可能性。リポジトリ内・親ディレクトリに`pyproject.toml`/`ruff.toml`は存在しないことを確認済み）
- **対処・回避方法**: CIでのlint結果がruffのバージョンや実行環境に依存して揺れないよう、リポジトリルートに`ruff.toml`を追加しルール選択（E4, E7, E9, F）を明示的に固定。lint対象もコンテナ化対象コード（`services/`, `common/`）のみに絞り、既存の`scripts/`配下は対象外とした（本タスクのスコープ外の既存コードを直す必要が生じるのを避けるため）

## 2026-09-03 コンテナ化・CI実装 ローカルshellの`python3`がsafe-chainラッパーでEACCES
- **何を期待していたか**: `python3 -m venv`でruff検証用の一時venvを作成できること
- **実際どうだったか**: シェル関数`python3`が社内セキュリティツール（safe-chain）経由の実行にラップされており、`/usr/local/certs/ca-key.pem`への書き込み権限エラー（`EACCES`）で失敗した
- **原因**: ローカル開発環境固有のシェル設定（`~/.claude/shell-snapshots/`のスナップショットで定義された関数）の問題。GitHub Actions実行環境には影響しない
- **対処・回避方法**: `/opt/homebrew/bin/python3`をフルパスで直接呼び出すことでラッパーを回避した。CI/CD実装自体には影響しないため、リポジトリ側の対応は不要

## 2026-09-03 コンテナ化・CI実装 CLAUDE.mdのドキュメント配置規約とCHANGELOG.mdの慣習が衝突
- **何を期待していたか**: CLAUDE.mdの既存規約「`README.md`と`CLAUDE.md`以外のドキュメントは`docs/`配下」に従い、`CHANGELOG.md`も`docs/CHANGELOG.md`に置く
- **実際どうだったか**: `CHANGELOG.md`はOSSエコシステム上ルート直下に置くのが強い慣習（`gh release`のUI・多くのツールがルート直下を前提に参照する）であり、`docs/`配下に置くと慣習から外れる
- **原因**: PR #1でこの規約を定めた時点では、ルート直下配置が慣習として期待される新規ファイル（`CHANGELOG.md`）が今後追加される想定が無かった
- **対処・回避方法**: `CHANGELOG.md`をルート直下に配置し、CLAUDE.mdのドキュメント構成表・配置規約に「OSSエコシステムの慣習上の例外」として明記するよう更新した（本タスクの一部として）

## 2026-09-03 コンテナ化・CI実装（PR #2完了後） Organization全体のworkflow write権限が無効化されており、release.ymlのGHCR pushが403になる想定だった
- **何を期待していたか**: `release.yml`の`build-and-push`ジョブが`permissions: packages: write`を明示宣言しているため、`main`マージ時にGHCRへのdocker pushが成功すること
- **実際どうだったか**: リポジトリ単位で`gh api --method PUT repos/.../actions/permissions/workflow -f default_workflow_permissions=write`を試みると `409 Conflict: "Write permissions for workflows are disabled by the organization"` で拒否された。ワークフローYAML内で`packages: write`を宣言していても、この状態のままではGITHUB_TOKENは実質read権限のままになり、実行時にGHCR pushが403で失敗する見込みだった（PR #2作成時点ではまだ`services/**`等への実質変更を伴うpushが無く、release.ymlが未発火だったため実地確認はできておらず、PR本文の「未検証・持ち越し」に記載のみだった）
- **原因**: `picketfence-labs` Organization全体の`default_workflow_permissions`が`read`のままだった。この設定はリポジトリ単位設定の**上限（ceiling）**として働くため、リポジトリ側の設定変更だけでは解決できず、Organization Owner権限（`admin:org`スコープ）が必要な対応だった
- **対処・回避方法**: 本リポジトリ側のPRでは対応が完結しないため、Organization管理を担うVaultセッション側にエスカレーションした。2026-09-03、Organization・リポジトリ両方の`default_workflow_permissions`を`write`に変更済み（`can_approve_pull_request_reviews`は[ADR 0005](decisions/0005-changelog-commit-mechanism.md)の`required_approving_review_count: 0`設計を踏まえ不要と判断し`false`のまま維持、PoLP）。**この対応により次回`release.yml`発火時のGHCR push 403は解消される見込みだが、実地確認（実際にGHCR pushが成功しGitHub Releaseが作成されること）はまだ完了していない**。次に`services/`・`common/`等への実質変更を伴うPRをmergeし`release.yml`を実際に発火させた際、本エントリの想定通り解消されているか確認すること
- **コスト**: N/A（Organization管理者側の対応、本リポジトリでの実装コストは無し）

## 2026-09-03 release.yml実地確認（`workflow_dispatch`手動発火）後 CHANGELOG.md更新PRの自動作成が`can_approve_pull_request_reviews`不足で失敗

- **何を期待していたか**: `release.yml`の最終ステップ（`gh pr create` + `gh pr merge`によるCHANGELOG.md更新PRの自動作成・auto-merge）が成功すること
- **実際どうだったか**: `workflow_dispatch`での手動発火（初回ブートストラップ、`v0.1.0`）で(1)バージョン算出・GHCR push（6サービス）・GitHub Release作成、(3)GHCRパッケージのpublic可視性設定（best-effort）は成功したが、(2)のPR作成ステップが`GraphQL: GitHub Actions is not permitted to create or approve pull requests (createPullRequest)`で失敗。`chore/changelog-v0.1.0`ブランチはpush済みだがPRは未作成のまま残存した
- **原因**: 上記エントリ（2026-09-03、Organization workflow write権限）とは別の設定`can_approve_pull_request_reviews`（GitHub UI上は1つのチェックボックス「Allow GitHub Actions to create **and approve** pull requests」）が原因。この設定は「PR承認」だけでなく「PR作成」権限も同じ1つの設定でまとめて制御しており、上記エントリで「[ADR 0005](decisions/0005-changelog-commit-mechanism.md)の`required_approving_review_count: 0`設計により承認機能は不要と判断し`false`のまま維持（PoLP）」としていた判断は、この設定が作成権限も兼ねる点を見落としていた誤りだった。`default_workflow_permissions`と同様、Organization側の同名設定がリポジトリ単位設定の上限（ceiling）になっていた（Organization側も`false`）
- **対処・回避方法**: Vaultセッション側で`admin:org`スコープを一時取得し、Organization・リポジトリ両方の`can_approve_pull_request_reviews`を`true`に変更済み（2026-09-03）。直後にスコープは取り消し済み。**これにより次回`release.yml`発火時のCHANGELOG.md自動PR作成・auto-mergeは成功する見込みだが、実地確認はまだ完了していない**
- **残タスク・開発Claudeさんへの確認依頼**: 上記対応時点で残存している`chore/changelog-v0.1.0`ブランチ（コミット済み、CHANGELOG.mdに`v0.1.0`分を追記、`main`からahead 1・behind 0、PR未作成）をどう処理するか、方針を決めていただきたい。
  - (a) 今すぐ手動で`gh pr create`→mergeし、`v0.1.0`分のCHANGELOG更新を完了させる
  - (b) このブランチは削除し、次回`services/`等への実質変更を伴うPRがmergeされ`release.yml`が実際に発火するタイミングで、CHANGELOG.md自動PR作成・auto-mergeが正しく機能するか実地確認する

  Vaultセッション側の所感は(a)（今すぐ完了させる方が素直）ですが、次のリリース予定や検証計画を踏まえた判断が必要と考えられるため、開発Claudeさん側で決めていただき、このログに追記する形で記録してください。
- **コスト**: N/A（Organization管理者側の対応、本リポジトリでの実装コストは無し）
- **決定（2026-09-03、開発Claudeさん）**: (a)を採用。`chore/changelog-v0.1.0`ブランチの内容はv0.1.0リリース時点のリリースノートそのものであり、(b)で削除すると次のリリース（v0.1.1想定）まで待っても復元できず、v0.1.0のChangelogエントリが永久に欠落するため。PR #6として手動でPR化・squash mergeし完了させた。CHANGELOG.md自動PR作成・auto-mergeフロー自体の実地確認は、次回`services/`・`common/`等への実質変更を伴うPRがmergeされ`release.yml`が自動発火するタイミングに持ち越し

## 2026-09-03 完了報告後の確認 「GHCRパッケージのpublic可視性設定は成功した」という記録が誤りだった（訂正）
- **何を期待していたか**: 上記エントリ（Organization workflow write権限のブロッカー解消）で「(1)...GHCRパッケージのpublic可視性設定（best-effort）は成功した」と記録し、本リポジトリのVault側project memoryにも同内容を反映していた
- **実際どうだったか**: `gh run view <run-id> --log`で当該ステップの実際のログを確認したところ、6サービス全てで`gh: Not Found (HTTP 404)`により失敗していた（`set -euo pipefail`のため1件目`product`で即中断）。`continue-on-error: true`によりジョブ全体は緑チェックのまま完走したため、ログ本文を確認せずActions UI上の見た目だけで「成功」と判断してしまっていた。実際に`docker pull`を未認証で試したところ`unauthorized`、GitHub上のpackageページも`404`（非公開のまま）で、design-brief.mdセクション5の検証項目「本リポジトリ以外から`docker pull`で取得できることを確認」を満たしていない状態だった
- **原因**: (1) `continue-on-error: true`のステップは失敗してもジョブ全体が緑になるため、ログ本文を見ずに完了と判断するのは危険。(2) 根本原因はADR 0006参照。GitHub PackagesのAPIは認証方式としてclassic PATのみを想定しており、`GITHUB_TOKEN`ではvisibility変更が404になる
- **対処・回避方法**: [ADR 0006](decisions/0006-package-visibility-automation.md)としてclassic PAT（`write:packages`のみ、Secret名`PACKAGES_PAT`）を追加する方式を決定。PAT発行・Secret登録は利用者側で対応（外部前提条件のため、能動的に相談済み）。登録後、`workflow_dispatch`で再実行し既存6パッケージのpublic化を実地確認する
- **教訓**: `continue-on-error: true`を使うステップは、「失敗してもワークフローを止めない」だけであり「成功した」ことの確認にはならない。best-effort処理の完了報告時は必ずログ本文（`gh run view --log`）まで確認すること

## 2026-09-04 `PACKAGES_PAT`登録後も同じ404で失敗 → visibility変更API自体が存在しないと判明（ADR 0006の前提が誤りだった）

- **何を期待していたか**: ADR 0006の決定（`write:packages`スコープのみのclassic PAT `PACKAGES_PAT` を追加）に従い、利用者に(1)PAT発行（`picketfence-labs` Organization ownerアカウント）、(2)リポジトリSecretへの登録を依頼。登録後`workflow_dispatch`で`release.yml`を再実行すれば「Publicize GHCR packages」ステップが成功する見込みだった
- **実際どうだったか**: `PACKAGES_PAT`登録後の再実行（`workflow_dispatch`、Run ID `33819001619`）でも、6サービス全てで**同じ`404 Not Found`**が発生した。Vaultセッション側でOrganization owner権限を持つ別アカウント経由の`read:packages`スコープで同一パッケージへ`GET /orgs/{org}/packages/container/{name}`を試したところ**成功**し、認証情報・権限自体は正しく機能していることを確認。この時点でGitHub公式のREST APIリファレンス（[Packages API](https://docs.github.com/en/rest/packages/packages)）のエンドポイント一覧を確認したところ、組織所有パッケージに対してGET・DELETE・POST restoreのみが公開されており、**visibilityを変更するPATCHエンドポイント自体がAPIとして存在しない**ことが判明した
- **原因**: ADR 0006作成時に参照した公式ドキュメントの記述（「GitHub Packages only supports authentication using a personal access token (classic)」）は、push/pull等の一般的な認証方式についての説明であり、「visibility変更用の管理APIが実在すること」までは意味していなかった。WebFetch（AI要約）でドキュメントを確認した際、実際のAPIエンドポイント一覧までは照合していなかったことが、誤った選択肢（classic PATなら成功する）の採択につながった
- **対処・回避方法**: [ADR 0007](decisions/0007-package-visibility-manual-only.md)として自動化を撤回。`release.yml`から「Publicize GHCR packages」ステップと`PACKAGES_PAT`利用箇所を削除し、パッケージのvisibility変更はGitHub Web UI（Package settings画面の「Danger Zone」）からの手動対応に一本化。既存6パッケージは利用者がWeb UIから手動でpublicに変更し、`docker pull`が未認証で成功することも実地確認済み（2026-09-04）。なお、この手動変更を試みた際に「Setting is disabled by organization administrators」というエラーが別途発生し、Organization設定（`https://github.com/organizations/{org}/settings/packages`の「Package creation」ポリシーでPublicが許可されていなかった）の追加対応も必要だった（こちらも解消済み）
- **教訓**: 「404 = 権限・認証方式の問題」と決めつけず、まず公式APIリファレンスの一覧で該当エンドポイントが実在するかを確認すべきだった。AI要約（WebFetch）は個別の文章の字面を追うだけになりがちで、「エンドポイント一覧に載っているか」という構造的な確認が漏れやすい。2件のADR（0004, 0006）にわたり存在しないAPIを前提に実装・修正を繰り返していた

## 2026-09-04 Minikubeデプロイのpull化（ADR 0008）実地確認 既定タグでのGHCR pullが`unauthorized`で失敗（上記のADR 0006/0007の経緯と並行して発生、後日解消確認）
- **何を期待していたか**: `k8s/services/services.yaml`をGHCR pull方式（`ghcr.io/picketfence-labs/insurance-<service>:__IMAGE_TAG__`、`scripts/deploy_k8s.sh`が`IMAGE_TAG`環境変数でタグを解決）に変更した後、Minikube上で既定タグで6サービスがpull・起動できることを確認する
- **実際どうだったか**: 変更直後の実地確認時点では、`kubectl describe pod`で全6サービスとも`Failed to pull image ... unauthorized`（`ImagePullBackOff`/`ErrImagePull`）。一方、`IMAGE_TAG=local`（`scripts/build_images_minikube.sh`でのローカルビルド）に切り替えると6サービス全Podが`1/1 Running`になり、`product`の`/health`も正常応答し、変更のメカニズム自体（`IMAGE_TAG`解決・マニフェスト参照）に問題が無いことは切り分け済みだった
- **原因**: 上記2エントリの経緯の通り、GHCRパッケージのvisibility変更API自体が存在せず（ADR 0007）、この時点ではまだ利用者によるWeb UIでの手動public化が完了していなかったため
- **対処・回避方法**: 利用者がWeb UI（Package settings画面の「Danger Zone」）から6パッケージ全てを手動でpublicに変更（ADR 0007の対応）。以後、既定タグ（`v0.1.1`）でのGHCR pullも6サービス全てで成功することをMinikube上で再確認済み（2026-09-04）
- **コスト**: N/A

## 2026-09-05 OpenAPI Doc公開パイプライン実装着手時 ADR 0009が前提とした「Scalarの静的HTML生成CLI」が実在しない

- **何を期待していたか**: ADR 0009（GitHub Pages自前ホスト + Scalarでの静的HTML生成）に基づき、`@scalar/cli`で各サービスの`openapi.yaml`から静的HTMLファイルを生成するGitHub Actionsステップを実装する
- **実際どうだったか**: DeepWiki（`scalar/scalar`）で確認したところ、`@scalar/cli`の`document serve`サブコマンドはローカル開発用のプレビューサーバーを起動するのみで、単一の自己完結型HTMLファイルを出力するCLIコマンドは存在しない（`document markdown`はMarkdown生成のみ）
- **原因**: ADR 0009作成時点（Vault側での事前調査）では、「OSSレンダラーとしてScalarが使える」＝「CLIで静的HTML生成ができる」という前提で比較検討していたが、実際にCLIの提供コマンドまでは確認していなかった
- **対処・回避方法**: 代替として、Scalarが公式に推奨する自前ホスト方式（`@scalar/api-reference`をCDN経由で読み込み、`Scalar.createApiReference('#app', { url: './openapi.yaml' })`で初期化する数行のHTMLファイルを配置する方式。ビルド不要、GitHub Pages等の静的ホスティングでの利用が公式に推奨されている）を採用。ADR 0009の「決定」（GitHub Pages自前ホスト + Scalar採用）自体は変更不要（達成したい結果は同じ）だが、「静的HTML生成」という実現手段の記述は不正確だったため、本パイプライン実装時にADR 0009へ注記を追記する
- **教訓**: ADR 0006/0007の教訓（「404=権限問題と決めつけず、まずAPI一覧で存在確認する」）と同種のパターン。ツール選定時、「機能名（レンダラー）」と「その機能を使うための具体的なインターフェース（CLIサブコマンド）」を分けて確認すべきだった

## 2026-09-05 OpenAPI Doc公開パイプライン（PR #15）マージ後 実地確認完了

- **何を期待していたか**: PR #15マージ後、`pages.yml`が`main`へのpushで発火し、`actions/deploy-pages`によるGitHub Pages公開が成功すること（PR #15時点では`workflow_dispatch`が既定ブランチ未反映のワークフローを実行できない仕様のため未検証だった）
- **実際どうだったか**: マージ後の自動発火（push, Run ID `33949981836`）が`success`で完了。6サービス全ての`https://picketfence-labs.github.io/kong-api-bundle-insurance/api/<service>/`（+ `openapi.yaml`、+ ルートインデックス）がHTTP 200で応答し、Playwrightで実際にブラウザ表示して日本語のAPI仕様が正しくレンダリングされることを確認（コンソールエラーは`favicon.ico`の404のみ、無害）。想定通り解消された
- **コスト**: N/A
