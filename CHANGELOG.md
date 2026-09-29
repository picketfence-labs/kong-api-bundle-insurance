# Changelog

このファイルは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) の形式に準拠する。
バージョンは `git tag`（`vX.Y.Z`）のみを正とし、`main` マージ時に GitHub Actions
（`.github/workflows/release.yml`）が新しいバージョンのセクションをここへ自動追記する
（詳細・判断根拠: [docs/design-brief.md](docs/design-brief.md)、[ADR 0002](docs/decisions/0002-changelog-method.md)、[ADR 0005](docs/decisions/0005-changelog-commit-mechanism.md)）。手動でセクションを追記する場合も、このファイルの直下（マーカーコメントの直後）に追加すること。

<!-- CHANGELOG_INSERT_MARKER: 新しいバージョンのセクションはこの直後に追記される -->
## [v0.1.2] - 2026-09-29

## What's Changed
* docs: CHANGELOG.md に v0.1.1 を追記 by @github-actions[bot] in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/10
* fix: GHCRパッケージのpublicize自動化を撤回、手動対応に一本化 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/11
* chore: settings.jsonにruff checkの許可を追加 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/12
* feat: Minikubeデプロイの標準経路をGHCR pullに変更（ADR 0007） by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/9
* docs: コンテナ説明改善（README再構成+OpenAPI Doc公開）の基本設計 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/13
* docs: READMEをコンテナ利用者向けに再構成 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/14
* ci: OpenAPI SpecをScalar+GitHub Pagesで公開するパイプラインを追加 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/15
* docs: OpenAPI Doc公開パイプラインの実地確認結果を記録 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/16
* docs: PRマージは人間が実行する運用に変更(gh pr mergeをdeny) by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/17
* docs: 全5箇所のMermaid図をArchifyへ移行 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/18
* fix: use Kubernetes service URLs in OpenAPI specs by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/19

## New Contributors
* @github-actions[bot] made their first contribution in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/10

**Full Changelog**: https://github.com/picketfence-labs/kong-api-bundle-insurance/compare/v0.1.1...v0.1.2

## [v0.1.1] - 2026-09-03

## What's Changed
* docs: can_approve_pull_request_reviewsブロッカー解消の記録と残ブランチの方針確認依頼 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/5
* docs: CHANGELOG.md に v0.1.0 を追記 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/6
* docs: chore/changelog-v0.1.0ブランチの処理方針決定を記録 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/7
* fix: GHCRパッケージのpublic可視性変更をclassic PAT経由に変更 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/8


**Full Changelog**: https://github.com/picketfence-labs/kong-api-bundle-insurance/compare/v0.1.0...v0.1.1

## [v0.1.0] - 2026-09-03

## What's Changed
* Dev Onboardingハーネスの導入（コンテナ化・GHCR公開の準備） by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/1
* 6サービスのコンテナ化・GHCR公開・バージョニング自動化を実装 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/2
* docs: Organization workflow write権限のブロッカー解消をtroubleshooting-logに記録 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/3
* release.ymlにworkflow_dispatchを追加（初回ブートストラップ用） by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/4

## New Contributors
* @shinichi-hashitani made their first contribution in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/1

**Full Changelog**: https://github.com/picketfence-labs/kong-api-bundle-insurance/commits/v0.1.0

