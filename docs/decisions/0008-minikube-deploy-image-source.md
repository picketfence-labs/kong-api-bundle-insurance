# ADR 0008: Minikubeデプロイのイメージ取得方式をローカルbuildからGHCR pullへ変更

- **日付**: 2026-09-04
- **状態**: 決定

## コンテキスト
これまで`k8s/services/services.yaml`は`insurance-<service>:local`イメージを参照し、`scripts/build_images_minikube.sh`で`minikube docker-env`配下に直接ビルドしたイメージを`imagePullPolicy: IfNotPresent`でそのまま使う構成だった（Harness定義段階の初期実装、`docs/ARCHITECTURE.md`に記載）。

一方、`docs/design-brief.md`セクション5の検証項目は「pushされたイメージが、本リポジトリ以外から`docker pull`で実際に取得できることを確認」であり、GHCR公開パイプライン（PR #2〜#8、#11）は実装済み。ローカルbuild方式のままだと、本リポジトリのMinikube検証自体では一度もこの「実際にGHCRから取得したイメージが動く」ことを確認しないまま運用することになり、design-brief.mdが目指す状態（公開イメージをそのまま利用可能にする）とMinikube上の実態が乖離する。

## 検討した選択肢
1. **標準のデプロイ経路をGHCR pullに切り替える**: `k8s/services/services.yaml`のイメージ参照を`ghcr.io/picketfence-labs/insurance-<service>:<tag>`に変更し、`scripts/deploy_k8s.sh`が`IMAGE_TAG`環境変数（既定は最新リリースタグ）でタグを解決してapply前にプレースホルダを置換する。ローカルbuildは`IMAGE_TAG=local`指定時のみ使う開発用の代替経路として残す（`build_images_minikube.sh`も同じ`ghcr.io/picketfence-labs/insurance-<service>:local`タグでビルドするよう変更し、`imagePullPolicy: IfNotPresent`によりMinikubeのDocker内に存在すればpullを試みない挙動を利用する）。
2. **ローカルbuildを標準のまま維持し、GHCR pullは別マニフェスト（例: `k8s/services/services.ghcr.yaml`）として追加する**: 既存の開発フローに影響を与えないが、マニフェストが二重管理になり、標準経路がGHCR pullに切り替わらないため「公開イメージが実際に動く」確認が引き続き行われない。
3. **ローカルbuildは廃止し、GHCR pull一本化（ローカル開発用の代替経路は用意しない）**: 最もシンプルだが、リリース前の未pushコード変更をMinikubeで試す手段が無くなり、開発体験が悪化する。

## 決定
選択肢1を採用する。

## 判断基準・根拠
- design-brief.mdが目指す「公開イメージがそのまま利用可能」という状態を、Minikube検証でも実際に確認できるようにする（利用者からの明示的な指示）
- `IMAGE_TAG`によるプレースホルダ置換は、既存の`deploy_k8s.sh`が採用済みのパターン（`sed`によるControl Plane ID埋め込み）を踏襲しており、実装・保守コストが小さい
- ローカル開発の代替経路（`IMAGE_TAG=local`）を残すことで、リリース前のコード変更検証という既存のユースケースを失わない

## 想定していたこと vs 実際どうだったか
- 想定通りだった点: マニフェストのプレースホルダ置換（`IMAGE_TAG`によるsed置換）自体は想定通り機能した。`IMAGE_TAG=local`（`scripts/build_images_minikube.sh`でMinikubeのDockerに直接ビルド）を指定した場合、6サービス全Podが`1/1 Running`になり、`product`の`/health`エンドポイントも正常応答することをMinikube上で実地確認した
- 想定と異なった点: 本ADR作成時点では既定タグ（GHCRからのpull）が`unauthorized`で失敗した。当初は[ADR 0006](0006-package-visibility-automation.md)（`PACKAGES_PAT`によるvisibility自動化）が未完了であることが原因と考えていたが、並行して進んでいた調査（[ADR 0007](0007-package-visibility-manual-only.md)）により、そもそもGHCRパッケージのvisibility変更用APIは存在せず、GitHub Web UIからの手動対応が唯一の手段であることが判明した。利用者がWeb UIで6パッケージを手動でpublicに変更した後、既定タグでのGHCR pullも6サービス全てで成功することをMinikube上で再確認した
- 結論: 本ADRのメカニズム（GHCR pullへの切り替え・`IMAGE_TAG`によるタグ解決・ローカル開発フォールバック）、および実際のpull自体（ADR 0007のvisibility手動対応後）の両方が動作することを確認済み

## 影響・トレードオフ
- GHCRパッケージのvisibilityは新規パッケージ作成時（＝新サービス追加時）のみ手動対応が必要（[ADR 0007](0007-package-visibility-manual-only.md)）。既存6パッケージは対応済みで、以後のバージョンアップpushでは設定が保持される
- `IMAGE_TAG`の既定値は新しいリリースが出るたびに手動更新が必要（本タスクのスコープ外。将来的には最新タグを自動解決する仕組みを検討する余地がある）

## 関連する決定
- [ADR 0004: コンテナレジストリの選定](0004-container-registry-choice.md)
- [ADR 0007: GHCRパッケージのpublic可視性変更は手動対応のみとする（自動化を撤回）](0007-package-visibility-manual-only.md)
