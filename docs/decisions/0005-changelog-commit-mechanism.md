# ADR 0005: 保護された `main` へのバージョン管理ファイル反映方式

- **日付**: 2026-09-03
- **状態**: 決定

## コンテキスト
ADR 0002で「GitHub Release + `CHANGELOG.md`の併用」を、ADR 0003で「`main`マージ時に自動実行」を決定した。しかし実装着手時に、`main`のbranch protection（`required_pull_request_reviews`設定、`enforce_admins: true`）はPR経由以外の変更を一律GH006で拒否することが判明した（PR #1でダミーコミットのpushにより実際に確認済み）。これは`GITHUB_TOKEN`によるbotのpushであっても例外なく適用されるため、release automationワークフローが`CHANGELOG.md`の更新を`main`へ直接コミットすることができない。この分岐はADR 0001〜0004のいずれでも扱っていなかった。

あわせて、バージョン番号自体をリポジトリにコミットする`VERSION`ファイルとして管理するか、`git tag`のみから導出するかも本ADRの対象とする。

## 検討した選択肢
1. **botがCHANGELOG.md更新のみのPRを自動作成し、その場でauto-merge**: release workflowが`git tag`から次バージョンを算出→6イメージbuild・push→`git tag`作成・push（branch保護の対象外）→GitHub Release作成→`CHANGELOG.md`更新のみを含むPRを作成し、`required_approving_review_count: 0`を利用してその場でmerge。`main`への直接pushの禁止という既存ルールは一貫して維持される。バージョン番号は`git tag`から導出し、`VERSION`ファイルは持たない（tagとファイルの二重管理・drift を避けるため）。
2. **branch protectionをRulesetsに移行し、release automation用actorにbypassを許可**: classic branch protectionをRulesetsへ切り替え、GitHub Actions（またはbot用App/PAT）を「required pull requestのbypass対象」に指定する。直接pushの仕組み自体は単純だが、PR #1で動作確認済みの保護方式を別方式に切り替えることになり、再検証が必要になる。
3. **CHANGELOG.mdの自動コミットをやめ、GitHub Releaseのみを正とする（ADR 0002の再検討）**: `CHANGELOG.md`を自動更新対象から外す。ADR 0002の決定（GitHub Release + CHANGELOG.mdの併用）を覆すことになる。

## 決定
選択肢1（botによるCHANGELOG.md更新PRの自動作成・即auto-merge、バージョンは`git tag`から導出）を採用する。

## 判断基準・根拠
- 利用者から明示的に選択肢1の指示を受けた（実装着手前に確認済み）
- 「`main`への直接pushは禁止」というCLAUDE.md記載のルールを、botによる自動化であっても一貫して例外なく維持できる（ADR 0003が前提とする「`main`へのmerge自体が実質的なレビューゲート」という設計思想とも整合する）
- PR #1で動作確認済みのbranch protection方式（classic protection）を変更せずに済み、再検証のコストが発生しない
- バージョン番号を`VERSION`ファイルとして別途管理すると、`git tag`との不整合（drift）が起こり得る。tagのみを正とすることで単一の情報源になる

## 想定していたこと vs 実際どうだったか
（実装着手時点。実際にrelease workflowを`main`マージで動かしてから追記する）

## 影響・トレードオフ
- CHANGELOG.md更新PRは`required_approving_review_count: 0`により人間のレビュー無しでmergeされる。これはADR 0003が前提とする「`main`へのmerge＝実質的なレビューゲート」から意図的に外れる例外だが、対象は機械的に生成される`CHANGELOG.md`の追記のみ（サービスコード・設定への変更は含まない）であり、リスクは限定的と判断する
- 将来、`required_approving_review_count`を1以上に引き上げた場合、このauto-merge運用は成立しなくなる（botの承認をどう扱うか再設計が必要になる）。branch protection設定を変更する際は本ADRの前提が崩れていないか確認すること
- バージョン番号を`git tag`のみから導出するため、tagが誤って削除・改変された場合に次バージョン計算がずれる可能性がある（tag自体の保護は`allow_deletions: false`が`main`ブランチにのみ適用され、tagには及ばない点に注意）

## 関連する決定
- [ADR 0002: Change Log方式](0002-changelog-method.md)
- [ADR 0003: リリース自動化トリガー](0003-release-automation-trigger.md)
