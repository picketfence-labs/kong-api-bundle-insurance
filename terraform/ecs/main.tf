# 共通のローカル値とデータソース。

locals {
  name = var.project_name

  # 6バックエンドサービス。host名(=Service Connect の discovery name)は
  # Konnect の Service 定義(host=product 等)と一致させる。
  services = ["product", "customer", "simulation", "application", "policy", "claim"]

  # simulation は永続データを持たないステートレスサービス。
  container_port = 8000
}

# Konnect スタックの出力(CP/TP エンドポイント)を参照する。
# 先に terraform/konnect を apply しておくこと。
data "terraform_remote_state" "konnect" {
  backend = "local"
  config = {
    path = var.konnect_remote_state_path
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  cp_endpoint = data.terraform_remote_state.konnect.outputs.control_plane_endpoint
  tp_endpoint = data.terraform_remote_state.konnect.outputs.telemetry_endpoint
  cp_host     = replace(local.cp_endpoint, "https://", "")
  tp_host     = replace(local.tp_endpoint, "https://", "")
}
