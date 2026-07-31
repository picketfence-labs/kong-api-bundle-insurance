variable "aws_region" {
  description = "デプロイ先の AWS リージョン。"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "リソース名・タグの接頭辞に使うプロジェクト名。"
  type        = string
  default     = "kong-insurance"
}

variable "vpc_cidr" {
  description = "作成する VPC の CIDR。"
  type        = string
  default     = "10.20.0.0/16"
}

variable "image_tag" {
  description = "各サービスのコンテナイメージタグ。scripts/build_push_ecr.sh でこのタグを push する。"
  type        = string
  default     = "latest"
}

variable "desired_count" {
  description = "各バックエンドサービスの希望タスク数。"
  type        = number
  default     = 1
}

variable "backend_cpu" {
  description = "バックエンドサービス1タスクの CPU ユニット。"
  type        = number
  default     = 256
}

variable "backend_memory" {
  description = "バックエンドサービス1タスクのメモリ(MiB)。"
  type        = number
  default     = 512
}

variable "kong_cpu" {
  description = "Kong DP タスクの CPU ユニット。"
  type        = number
  default     = 512
}

variable "kong_memory" {
  description = "Kong DP タスクのメモリ(MiB)。"
  type        = number
  default     = 1024
}

variable "konnect_remote_state_path" {
  description = "Konnect スタックのローカル state ファイルへの相対パス。CP/TP エンドポイントの取得に使う。"
  type        = string
  default     = "../konnect/terraform.tfstate"
}

variable "dp_cert_path" {
  description = "Kong DP クライアント証明書(PEM)のパス。Konnect スタックが certs/ に生成したもの。"
  type        = string
  default     = "../../certs/tls.crt"
}

variable "dp_key_path" {
  description = "Kong DP クライアント秘密鍵(PEM)のパス。"
  type        = string
  default     = "../../certs/tls.key"
}
