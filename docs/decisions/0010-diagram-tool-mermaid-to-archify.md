# ADR 0010: ダイアグラム作成ツールをmermaidからArchifyへ移行

- **日付**: 2026-09-10
- **状態**: 決定

## コンテキスト
本リポジトリの5箇所（`README.md`、`docs/ARCHITECTURE.md`、`docs/design-brief.md`、`docs/INSTRUCTIONS.md`、`docs/DATA.md`）にMermaid図があり、`CLAUDE.md`にも「ダイアグラムはすべてmermaid形式で記述する」というルールが明記されていた。開発元のPicketfence Labs Vaultで、ノート・成果物用途の作図ツールをMermaidからArchify（`tt-a1i/archify`、自己完結型インタラクティブHTMLダイアグラムを生成するOSSツール）へ全面移行する方針が確定し、その実地適用として本リポジトリの既存Mermaid図もArchifyへ切り替える。

## 検討した選択肢
1. **現状維持（Mermaid継続）**: 追加コスト無し。GitHub上で`.md`を開くだけで即座に図が見える利点を維持できる
2. **Archifyへ全面移行し、生成HTMLをGitHub Pagesでホストしてリンク**: 見た目の完成度（配色による意味分類・凡例・境界ボックス・パン/ズーム/検索等のインタラクティブ機能）が明確に向上する。ただしGitHubのMarkdownサニタイズにより生成HTMLを直接埋め込むことはできず、「静的画像＋リンク」の間接的な埋め込みが必要になり、Mermaidのような「ページを開けば即座に図が見える」体験は失われる

## 決定
選択肢2（Archifyへ全面移行）を採用する。

## 判断基準・根拠
- Picketfence Labs Vault側で、ノート・成果物用途の作図ツールをArchifyへ統一する方針が既に確定しており、本リポジトリはその実地検証（3件目）を兼ねる
- 「資料として通用する完成度」を重視する利用者の意向があり、GitHub上での即時プレビューという利便性よりも見た目の完成度を優先する判断が成立する

## 実装方式
- Archifyの生成HTMLは`picketfence-labs/diagrams`（GitHub Pages、Public）へ公開し、本リポジトリのMarkdown側は静的PNG（`docs/images/`に格納）をインタラクティブ版HTMLへのリンクにする形式（`[![タイトル](docs/images/xxx.png)](https://picketfence-labs.github.io/diagrams/<slug>/)`）で埋め込む
- ダイアグラムのソース（JSON IR）は本リポジトリには含めない。Picketfence Labs Vault側の対応Projectが正本を管理する
- `CLAUDE.md`の「ダイアグラムはすべてmermaid形式で記述する」ルールを本ADRの内容に合わせて更新済み

## 影響・トレードオフ
- GitHub上で`.md`ファイルを開いた瞬間に図が見える体験は失われる（静的PNGは見えるが、インタラクティブ性を得るには別タブでリンク先を開く一手間が必要になる）
- ダイアグラムの追加・更新が、テキストエディタでの直接編集（Mermaid）から、Archify skillでのJSON IR作成→validate→deliver→PNG書き出し→`picketfence-labs/diagrams`への公開、という複数ステップの作業に変わり、変更コストが増す
- `docs/DATA.md`のER図はArchifyに専用の図種別が無いため、`architecture`種別（`database`バリアントコンポーネント＋カーディナリティ付きラベル）で代替表現している。標準的なER記法（crow's-foot記法、属性一覧）ほど厳密ではない

## 関連する決定
- なし（本リポジトリで初めてダイアグラムツールに関する判断ポイントが発生したため）
