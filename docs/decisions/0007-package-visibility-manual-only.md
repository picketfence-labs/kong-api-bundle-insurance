# ADR 0007: GHCRパッケージのpublic可視性変更は手動対応のみとする（自動化を撤回）

- **日付**: 2026-09-04
- **状態**: 決定

## コンテキスト
[ADR 0006](0006-package-visibility-automation.md)で、`release.yml`の「Publicize GHCR packages」ステップが`GITHUB_TOKEN`では404になる原因を「GitHub Packages管理APIはclassic PATのみ対応のため」と結論し、`write:packages`スコープのみのclassic PAT（Secret: `PACKAGES_PAT`、Organization ownerアカウントで発行）を追加する対応を実施した。

しかし`PACKAGES_PAT`登録後に`workflow_dispatch`で`release.yml`を再実行しても、**同じ`404 Not Found`で失敗し続けた**。Vaultセッション側で切り分けのため、Organization owner権限を持つ別アカウント経由で`read:packages`スコープを一時取得し、対象パッケージ（`insurance-product`等）のメタデータ取得（`GET /orgs/{org}/packages/container/{name}`）を試したところ**成功**した。つまり認証情報・権限自体は正しく機能しており、GETは通るがPATCHだけが404になる状態だった。

この時点でGitHub公式のREST APIリファレンス（[Packages API](https://docs.github.com/en/rest/packages/packages)）のエンドポイント一覧を確認したところ、組織所有パッケージに対して公開されているエンドポイントは以下のみだった:
- `GET /orgs/{org}/packages` / `GET /orgs/{org}/packages/{package_type}/{package_name}`（一覧・取得）
- `DELETE /orgs/{org}/packages/{package_type}/{package_name}`（削除）
- `POST /orgs/{org}/packages/{package_type}/{package_name}/restore`（復元）

**visibilityを変更するPATCHエンドポイントはドキュメント上に存在しない**。ADR 0006作成時に参照した「GitHub Packages only supports authentication using a personal access token (classic)」という記述は、push/pull等の一般的な認証方式についての説明であり、「visibility変更用の管理APIが実在すること」を保証するものではなかった。これはAI要約（WebFetch）でドキュメントを確認した際、実際のAPIエンドポイント一覧までは照合していなかったことに起因する誤読だった。

## 検討した選択肢
1. **GraphQL APIでの代替実装を探す**: GitHub GraphQL API（`PackageVersion`, `Package`型等）にvisibility変更用のmutationが存在するか調査する。→ 本調査の範囲では、GraphQL スキーマ上にもpackage visibilityを変更するmutationは見当たらなかった（GitHub CLI・Web UI以外にvisibility変更の公式な手段が無いという結論を補強）
2. **`gh api`ではなくブラウザ操作の自動化（Playwrightなどによるスクレイピング）で代替する**: GitHub Web UIの「Package settings」ページを自動操作してvisibility変更を行う。技術的には可能だが、非公式な手段（UI変更で容易に壊れる、GitHub利用規約上のリスク、実装・保守コストが高い）であり、既存のCIワークフロー（`release.yml`）の設計方針（公式APIのみを使う）から逸脱するため不採用
3. **自動化を撤回し、パッケージのvisibility変更は手動（GitHub Web UI）のみとする**: ADR 0006検討時点でも選択肢3として一度検討されていたが、「design-brief.mdの完全自動化要件から後退する」という理由で不採用にされていた。しかし選択肢1・2が非現実的と判明した以上、**そもそも自動化する公式な手段が存在しない**ため、この選択肢が唯一の現実的な対応となる

## 決定
選択肢3（`release.yml`から「Publicize GHCR packages」ステップを削除し、パッケージのvisibility変更は都度手動でGitHub Web UI（Package settings画面の「Danger Zone」→「Change package visibility」）から行う）を採用する。

`PACKAGES_PAT` Secretは今後不要になるため削除する。

## 判断基準・根拠
- API自体が存在しない以上、「完全自動化」は技術的に選択肢として成立しない。存在しない前提の上に実装を積み増すこと自体が誤り
- パッケージのvisibilityは一度publicに設定すれば、同一パッケージ名への以後のpush（バージョンアップ等）では設定が保持される（ADR 0006の選択肢3検討時の分析の通り）。visibility変更が必要になるのは**新規パッケージ作成時のみ**であり、これは新サービス追加時に限られるため頻度は低い
- 使われなくなった長期間有効な資格情報（`PACKAGES_PAT`）を残しておくこと自体がPoLP・セキュリティ上望ましくないため、Secretごと削除する

## 想定していたこと vs 実際どうだったか
- 想定（ADR 0004・0006時点）: GHCRパッケージのvisibility変更は、認証方式さえ正しければAPI経由で自動化できる
- 実際: そもそもvisibility変更用のREST/GraphQL APIが公式に提供されておらず、GitHub Web UIでの手動操作が唯一の手段だった。2件のADR（0004, 0006）にわたり誤った前提の上で実装・修正を繰り返していたことになる
- **教訓**: 「404 = 権限・認証の問題」と決めつけず、そもそも呼び出し先のAPIが存在するかを一覧（Reference）で確認するステップを先に踏むべきだった。特に、AI要約（WebFetch）でのドキュメント確認は個別の記述の字面を追うだけになりがちで、「エンドポイント一覧に載っているか」という構造的な確認が漏れやすい

## 影響・トレードオフ
- 新サービス追加時、対応者（利用者 or 開発Claudeさん経由での利用者依頼）は忘れずに手動でpublicize設定を行う必要がある。`docs/troubleshooting-log.md`・`CLAUDE.md`のサービス追加手順にこの手動ステップを明記し、失念を防ぐ
- `release.yml`から「Publicize GHCR packages」ステップと`PACKAGES_PAT`利用箇所が無くなり、ワークフローがシンプルになる（呼び出し先が存在しないAPIを叩き続ける無意味なコードが除去される）

## 関連する決定
- [ADR 0004: コンテナレジストリの選定](0004-container-registry-choice.md)
- [ADR 0006: GHCRパッケージのpublic可視性変更を自動化する認証方式](0006-package-visibility-automation.md)（本ADRにより廃止）
