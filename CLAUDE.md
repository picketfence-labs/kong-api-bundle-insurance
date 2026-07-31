# CLAUDE.md — 本リポジトリでの取り決め

このファイルは、本リポジトリで作業する際の方針・取り決めをまとめたものです。

## プロジェクトの目的

Kong Gateway Enterprise 3.15 + Kong Konnect を前段に置き、損害保険ドメインの
6サンプルAPI（product / simulation / customer / application / policy / claim）を
稼働させるデモ環境。**このリポジトリは公開予定**。まず Docker Compose、後工程で AWS ECS。

## ドキュメント構成の取り決め

| ファイル | 役割 |
|---|---|
| `README.md` | リポジトリのREADME。プロジェクト概要と利用方法（ルート直下） |
| `CLAUDE.md` | 本ファイル。指示・取り決めのまとめ（ルート直下） |
| `docs/DATA.md` | データモデル定義と設計判断の記録 |
| `docs/ARCHITECTURE.md` | 全体構成・技術的な説明 |
| `docs/INSTRUCTIONS.md` | 環境の構築手順 |

- `README.md` と `CLAUDE.md` **以外**のドキュメントは `docs/` 配下に置く。
- **ダイアグラムはすべて mermaid 形式で記述する**（```` ```mermaid ````）。ASCIIアートは使わない。GitHub・claude.ai のどちらでもレンダリングされる構文を用いる。

## 設計・実装の方針

- **言語/FW**: 全サービス Python / FastAPI で統一。
- **データ**: すべて日本語。日本のフォーマット（郵便番号・都道府県・電話番号・マイナンバー等）に準拠。
  マイナンバーは総務省告示のチェックデジット算出方法に準拠したダミー値。
- **テストデータ**: 全サービスをまたいで参照整合性を担保する（`scripts/generate_test_data.py` で一括生成）。
  商品カテゴリと請求種別の整合など、ドメイン的な矛盾を作らない。
- **商品ドメイン**: 損害保険会社を想定。生命保険・学資保険は扱わない。
- **マイナンバーのAPI公開**: 現状は raw（フル桁）で返却。将来、利用者ロールに応じて raw/masked を切り替える。
- **Konnect / IaC**: Control Plane・Service・Route・DP証明書はすべて **Terraform**（`terraform/`、Kong/konnect provider）で管理する。decK は使用しない。最初は Service と Route のみを定義し、認証等のプラグインは後日 Terraform で追加。
- **Konnect 反映先**: US リージョン / 組織 `hashi-sandbox` / Control Plane `kong-insurance-demo`。

## データモデル変更のワークフロー

データモデルはユーザーが実施前に確認する。ドラフトを提示し、修正指示を受けてから実装に進む。
変更は `docs/DATA.md` に反映し、確定後に `scripts/generate_test_data.py` と各サービスのモデルを更新する。

## 秘匿情報の取り扱い

- `KONNECT_PAT` などのトークンは環境変数で渡す。**リポジトリにコミットしない**。
- `.env`、`certs/`（DP証明書）、`terraform.tfvars`、`*.tfstate` は `.gitignore` 済み。`.env.example` / `terraform.tfvars.example` のみコミットする。
- Terraform の PAT は `TF_VAR_konnect_pat` 環境変数で渡す（tfvars に書かない）。
