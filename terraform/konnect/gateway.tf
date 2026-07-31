# Service と Route を定義する(現段階では認証等のプラグインは付けない)。
# 6サービスは同一構造のため for_each でまとめて定義する。
# host は docker-compose のサービス名に一致させ、Kong DP が同一ネットワーク内の
# バックエンドへプロキシする。

locals {
  # サービス名 => 公開パス
  services = {
    product     = "/product"
    customer    = "/customer"
    simulation  = "/simulation"
    application = "/application"
    policy      = "/policy"
    claim       = "/claim"
  }
}

resource "konnect_gateway_service" "svc" {
  for_each = local.services

  control_plane_id = konnect_gateway_control_plane.insurance.id
  name             = each.key
  host             = each.key
  port             = 8000
  protocol         = "http"
  tags             = ["insurance", each.key]
}

resource "konnect_gateway_route" "route" {
  for_each = local.services

  control_plane_id = konnect_gateway_control_plane.insurance.id
  name             = "${each.key}-route"
  paths            = [each.value]
  strip_path       = true
  tags             = ["insurance", each.key]

  service = {
    id = konnect_gateway_service.svc[each.key].id
  }
}
