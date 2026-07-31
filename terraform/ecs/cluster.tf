# ECS クラスタ・Service Connect 用ネームスペース・ロググループ。

resource "aws_ecs_cluster" "this" {
  name = local.name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  cluster_name       = aws_ecs_cluster.this.name
  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

# Service Connect のネームスペース。バックエンドは discovery name(=サービス名)で
# 相互解決され、Kong DP は http://product:8000 等でアクセスできる
# (Konnect の Service host=product と一致)。
resource "aws_service_discovery_http_namespace" "this" {
  name        = local.name
  description = "Service Connect namespace for ${local.name}"
}

resource "aws_cloudwatch_log_group" "svc" {
  for_each          = toset(local.services)
  name              = "/ecs/${local.name}/${each.key}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "kong_dp" {
  name              = "/ecs/${local.name}/kong-dp"
  retention_in_days = 14
}
