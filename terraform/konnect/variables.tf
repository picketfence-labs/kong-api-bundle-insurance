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

# Data Plane のクライアント証明書は Kong Operator が KonnectExtension の
# clientAuth(provisioning: Automatic)で自動発行・登録するため、Terraform では
# 証明書を扱わない。
