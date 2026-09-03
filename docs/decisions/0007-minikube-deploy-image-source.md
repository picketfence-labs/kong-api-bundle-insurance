# ADR 0007: Minikubeデプロイのイメージ取得方式をローカルbuildからGHCR pullへ変更

- **日付**: 2026-09-04
- **状態**: 決定

## コンテキスト
これまで`k8s/services/services.yaml`は`insurance-<service>:local`イメージを参照し、`scripts/build_images_minikube.sh`で`minikube docker-env`配下に直接ビルドしたイメージを`imagePullPolicy: IfNotPresent`でそのまま使う構成だった（Harness定義段階の初期実装、`docs/ARCHITECTURE.md`に記載）。

一方、`docs/design-brief.md`セクション5の検証項目は「pushされたイメージが、本リポジトリ以外から`docker pull`で実際に取得できることを確認」であり、GHCR公開パイプライン（PR #2〜#8）は実装済み。ローカルbuild方式のままだと、本リポジトリのMinikube検証自体では一度もこの「実際にGHCRから取得したイメージが動く」ことを確認しないまま運用することになり、design-brief.mdが目指す状態（公開イメージをそのまま利用可能にする）とMinikube上の実態が乖離する。

## 検討した選択肢
1. **標準のデプロイ経路をGHCR pullに切り替える**: `k8s/services/services.yaml`のイメージ参照を`ghcr.io/picketfence-labs/insurance-<service>:<tag>`に変更し、`scripts/deploy_k8s.sh`が`IMAGE_TAG`環境変数（既定`v0.1.0`）でタグを解決してapply前にプレースホルダを置換する。ローカルbuildは`IMAGE_TAG=local`指定時のみ使う開発用の代替経路として残す（`build_images_minikube.sh`も同じ`ghcr.io/picketfence-labs/insurance-<service>:local`タグでビルドするよう変更し、`imagePullPolicy: IfNotPresent`によりMinikubeのDocker内に存在すればpullを試みない挙動を利用する）。
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
- 想定通りだった点（悪い意味で）: 既定の`IMAGE_TAG=v0.1.0`（GHCRからのpull）は、想定通り失敗した。`kubectl describe pod`で`Failed to pull image ... unauthorized`を確認。原因は[ADR 0006](0006-package-visibility-automation.md)のPR #8がまだマージされておらず`PACKAGES_PAT` Secretも未登録のため、全6パッケージが非公開のまま残っていること。本ADRの変更自体のバグではなく、既知の外部前提条件（利用者側でのPAT発行・Secret登録）が未解消なことによるもの
- 結論: 本ADRのメカニズム（GHCR pullへの切り替え・`IMAGE_TAG`によるタグ解決・ローカル開発フォールバック）は実装・動作として正しいことを確認済み。ADR 0006の対応（`PACKAGES_PAT`登録・PR #8マージ・パッケージpublic化）が完了次第、`IMAGE_TAG=v0.1.0`（既定）でのpullも成功する見込み

## 影響・トレードオフ
- GHCRパッケージが非公開の間（[ADR 0006](0006-package-visibility-automation.md)の対応完了まで）は、標準のデプロイ経路（`IMAGE_TAG=v0.1.0`）でも`ImagePullBackOff`になる。開発用の`IMAGE_TAG=local`経路は影響を受けない
- `IMAGE_TAG`の既定値（`v0.1.0`）は新しいリリースが出るたびに手動更新が必要（本タスクのスコープ外。将来的には最新タグを自動解決する仕組みを検討する余地がある）

## 関連する決定
- [ADR 0004: コンテナレジストリの選定](0004-container-registry-choice.md)
- [ADR 0006: GHCRパッケージのpublic可視性変更を自動化する認証方式](0006-package-visibility-automation.md)
