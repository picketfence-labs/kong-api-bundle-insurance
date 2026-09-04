# ADR 0006: GHCRパッケージのpublic可視性変更を自動化する認証方式

- **日付**: 2026-09-03
- **状態**: **廃止（Superseded）** — 2026-09-04、[ADR 0007](0007-package-visibility-manual-only.md)により置き換え。本ADRの前提（classic PATなら成功する）自体が誤りだったため、本文はそのまま残し「想定していたこと vs 実際どうだったか」に追記する形で訂正する

## コンテキスト
`release.yml`の「Publicize GHCR packages (best-effort)」ステップ（ADR 0004で「pushしただけでは自動的にpublicにならない場合がある」と想定していたリスクへの対処）は、`GITHUB_TOKEN`を使って`PATCH /orgs/{org}/packages/container/{name}` APIを呼び出していた。2026-09-03の`workflow_dispatch`実地発火で、全6パッケージが`404 Not Found`で失敗していたことが判明した（`continue-on-error: true`により以降のジョブは継続したため、Actions UI上は目立たず見落とされた）。

GitHub公式ドキュメント（`about-permissions-for-github-packages`）を確認したところ、「GitHub Packages only supports authentication using a personal access token (classic)」と明記されており、`GITHUB_TOKEN`（Actionsトークン）やfine-grained PATはそもそもGitHub Packages管理API（visibility変更を含む）の認証方式として想定されていない。これが今回の404の直接原因であり、単なるスコープ不足ではなく認証方式自体が非対応だった。

その結果、6サービスのGHCRパッケージは現在も非公開のままで、`docs/design-brief.md`セクション5の検証項目「本リポジトリ以外から`docker pull`で実際に取得できることを確認」を満たしていない状態にある。

## 検討した選択肢
1. **classic PAT（`write:packages`スコープのみ）を新規Secret（`PACKAGES_PAT`）として追加し、「Publicize」ステップだけそのPATを使う**: 他のステップ（build・push・Release作成・CHANGELOG.md PR作成等）は`GITHUB_TOKEN`のまま維持し、影響範囲をvisibility変更の1ステップに限定する。PATはpicketfence-labs Organizationのowner権限を持つアカウントで発行する必要がある（GitHub Packagesの仕様上、organization ownerは配下パッケージへadmin権限を持つため）。
2. **classic PATに`repo`スコープも追加**: 一部の環境（非公開リポジトリ由来のパッケージ）では`repo`スコープが必要という報告があるが、本リポジトリ・パッケージは元から公開設定のため不要と判断。
3. **自動化を諦め、手動publicizeのみとする**: パッケージのvisibilityは一度publicに設定すれば、同一パッケージ名への以後のpushでは保持される（新規パッケージ作成時のみ再度必要になる）。新サービス追加は稀なため、都度手動対応でも実害は小さい。ただし「mainマージで完全に自動化される」というdesign-brief.mdの要件（セクション2「今回のスコープ」）からは後退する。

## 決定
選択肢1（`write:packages`スコープのみのclassic PATを`PACKAGES_PAT`として追加し、「Publicize」ステップのみで使用）を採用する。

## 判断基準・根拠
- 利用者から明示的に選択肢1の指示を受けた（実装着手前に確認済み）
- 最小権限（PoLP）: 新規PATのスコープを`write:packages`のみに絞り、既存の`GITHUB_TOKEN`ベースの他ステップ（build・push・Release作成等）には影響させない
- design-brief.mdが要求する「mainマージ時の完全自動化」を維持できる

## PAT発行・Secret登録（利用者側で対応、本ADRの実行権限外）
以下は組織admin権限・資格情報発行を伴うため、Claude Codeでは実行できない。利用者側で対応する:
1. `picketfence-labs` Organization ownerのアカウントで、`write:packages`スコープのみのclassic PATを発行
2. 本リポジトリのSecretsに`PACKAGES_PAT`として登録
3. 登録後、`workflow_dispatch`で`release.yml`を再実行し、既存6パッケージのpublic化を実地確認する（登録前のマージでは`release.yml`は`services/**`等のpathsフィルタに引っかからない限り発火しないため、意図せず失敗が再発することはない）

## 想定していたこと vs 実際どうだったか
- 想定: `GITHUB_TOKEN`に`packages: write`権限を宣言していれば、visibility変更APIも通る（ADR 0004時点ではこの区別を認識していなかった）
- 実際: GitHub PackagesのAPIは認証方式としてclassic PATのみを想定しており、`GITHUB_TOKEN`では404になる。`continue-on-error: true`によりワークフロー全体は成功表示のまま終わり、実際にログを確認するまで気づけなかった
- **さらなる訂正（2026-09-04）**: 本ADRの決定に従い`PACKAGES_PAT`（`write:packages`スコープのみのclassic PAT、Organization ownerアカウントで発行）を登録し`workflow_dispatch`で再実行したが、**同じ404で失敗し続けた**。Vaultセッション側でGitHub公式APIリファレンス（Packages API、`https://docs.github.com/en/rest/packages/packages`）のエンドポイント一覧を確認したところ、組織所有パッケージに対してGET（取得・一覧）・DELETE（削除）・POST restore（復元）は存在するが、**visibilityを変更するPATCHエンドポイント自体がAPIとして存在しない**ことが判明した。つまり404の原因は認証方式（`GITHUB_TOKEN` vs classic PAT）の違いではなく、そもそも呼び出し先のAPIが存在しないことだった。本ADR作成時の「GitHub Packages only supports authentication using a personal access token (classic)」という公式ドキュメントの記述は、pushやpull等の通常操作についての一般的な認証方式の説明であり、「visibility変更の管理APIが存在する」ことまでは意味していなかった。WebFetch（AI要約）でドキュメントを確認した際、実際のAPIエンドポイント一覧までは照合していなかったことが誤った選択肢1採択の直接原因。詳細は[ADR 0007](0007-package-visibility-manual-only.md)参照

## 影響・トレードオフ
- `PACKAGES_PAT`は長期間有効な資格情報のため、失効・ローテーション管理が必要になる（有効期限を設定し、期限管理を利用者側で行うことを推奨）
- Secret登録が完了するまでの間、新規パッケージ（将来サービスを追加した場合）は自動でpublic化されない。既存6パッケージについても、登録・再実行が完了するまでは非公開のまま

## 関連する決定
- [ADR 0004: コンテナレジストリの選定](0004-container-registry-choice.md)
