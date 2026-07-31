variable "konnect_pat" {
  description = "Kong Konnect Personal Access Token。環境変数 TF_VAR_konnect_pat で渡すこと(tfvarsには書かない)。"
  type        = string
  sensitive   = true
}

variable "konnect_server_url" {
  description = "Konnect API のエンドポイント(リージョン)。us/eu/au に応じて変更する。"
  type        = string
  default     = "https://us.api.konghq.com"
}

variable "control_plane_name" {
  description = "作成する Control Plane 名。"
  type        = string
  default     = "kong-insurance-demo"
}

variable "control_plane_description" {
  description = "Control Plane の説明。"
  type        = string
  default     = "保険ドメイン APIバンドル (product/simulation/customer/application/policy/claim) のデモ用 Control Plane"
}

variable "generate_dp_certificate" {
  description = "Kong Data Plane 接続用の自己署名証明書を生成し、Control Plane に登録するか。ローカルで DP を起動する場合は true。"
  type        = bool
  default     = true
}

variable "dp_cert_output_dir" {
  description = "生成した DP 証明書・鍵の出力先ディレクトリ(リポジトリルートからの相対)。"
  type        = string
  default     = "../certs"
}
