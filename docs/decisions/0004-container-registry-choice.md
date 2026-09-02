# ADR 0004: コンテナレジストリの選定

- **日付**: 2026-09-02
- **状態**: 決定

## コンテキスト
6サービスのコンテナイメージをどのパブリックコンテナレジストリへ公開するかを決める必要がある。Picketfence Labsは別プロジェクト（GCPインフラ整備）で、公開イメージはGitHub Container Registry（GHCR）、非公開イメージはGoogle Cloud Artifact Registryを使い分ける方針を既に決定している。

## 検討した選択肢
1. **GHCR（`ghcr.io/picketfence-labs/...`）を使う**: 既存のGitHub org方針を継承。追加のクラウド認証設定が不要（GitHub Actionsの`GITHUB_TOKEN`でpush可能）。他デモ・プロジェクトからの参照もGitHub org内で完結する。
2. **GCP Artifact Registry（publicリポジトリ設定）を使う**: 既にPicketfence Labs全体のGCPインフラ整備プロジェクトでArtifact Registryリポジトリ（非公開用）が構築済み。同じ基盤上にpublicリポジトリを追加することも技術的には可能。ただしこれは公開イメージ=GHCRという既定方針を崩すことになり、GCPインフラ側の設計変更も伴う。

## 決定
選択肢1（GHCR一本化）を採用する。

## 判断基準・根拠
- 別プロジェクト（GCPインフラ整備）のADRで、公開イメージはGHCR・非公開はArtifact Registryという使い分け方針が既に確定しており、本リポジトリのイメージは全て公開想定のため、その方針にそのまま従うのが整合的
- GitHub Actions上でのpushにGCP認証（Workload Identity Federation等）を追加で構築する必要がなく、実装コストが小さい
- 利用者からも「GHCRを使う（既定方針を継承）」との明示的な確認を得た

## 想定していたこと vs 実際どうだったか
（Harness定義段階のため未実装。実際にCIパイプラインを運用してから追記する）

## 影響・トレードオフ
- 将来、本リポジトリに非公開にすべきサービスが追加された場合、Artifact Registry側との連携（別レジストリへの分離push）を追加で設計する必要がある
- GHCRのpublic可視性設定（リポジトリのpackage設定でvisibilityをpublicにする操作）は、pushしただけでは自動的にpublicにならない場合がある点に注意し、実装タスクで確認する

## 関連する決定
- [ADR 0001: バージョニング粒度](0001-versioning-granularity.md)
- [ADR 0003: リリース自動化トリガー](0003-release-automation-trigger.md)
