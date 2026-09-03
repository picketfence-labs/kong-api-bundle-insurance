# Changelog

このファイルは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) の形式に準拠する。
バージョンは `git tag`（`vX.Y.Z`）のみを正とし、`main` マージ時に GitHub Actions
（`.github/workflows/release.yml`）が新しいバージョンのセクションをここへ自動追記する
（詳細・判断根拠: [docs/design-brief.md](docs/design-brief.md)、[ADR 0002](docs/decisions/0002-changelog-method.md)、[ADR 0005](docs/decisions/0005-changelog-commit-mechanism.md)）。手動でセクションを追記する場合も、このファイルの直下（マーカーコメントの直後）に追加すること。

<!-- CHANGELOG_INSERT_MARKER: 新しいバージョンのセクションはこの直後に追記される -->
## [v0.1.0] - 2026-09-03

## What's Changed
* Dev Onboardingハーネスの導入（コンテナ化・GHCR公開の準備） by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/1
* 6サービスのコンテナ化・GHCR公開・バージョニング自動化を実装 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/2
* docs: Organization workflow write権限のブロッカー解消をtroubleshooting-logに記録 by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/3
* release.ymlにworkflow_dispatchを追加（初回ブートストラップ用） by @shinichi-hashitani in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/4

## New Contributors
* @shinichi-hashitani made their first contribution in https://github.com/picketfence-labs/kong-api-bundle-insurance/pull/1

**Full Changelog**: https://github.com/picketfence-labs/kong-api-bundle-insurance/commits/v0.1.0

