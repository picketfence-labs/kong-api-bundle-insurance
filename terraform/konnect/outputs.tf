output "control_plane_id" {
  description = "作成された Control Plane の ID"
  value       = konnect_gateway_control_plane.insurance.id
}

output "control_plane_endpoint" {
  description = "Data Plane が接続する Control Plane エンドポイント"
  value       = konnect_gateway_control_plane.insurance.config.control_plane_endpoint
}

output "telemetry_endpoint" {
  description = "Data Plane のテレメトリ送信先エンドポイント"
  value       = konnect_gateway_control_plane.insurance.config.telemetry_endpoint
}

# docker compose --profile konnect up 用の .env に貼り付ける値。
# エンドポイントから https:// を除き :443 を付与する。
output "dp_env" {
  description = "Kong DP 起動用の .env に貼り付ける接続情報"
  value       = <<-EOT
    KONNECT_CP_ENDPOINT=${replace(konnect_gateway_control_plane.insurance.config.control_plane_endpoint, "https://", "")}:443
    KONNECT_CP_SERVER_NAME=${replace(konnect_gateway_control_plane.insurance.config.control_plane_endpoint, "https://", "")}
    KONNECT_TP_ENDPOINT=${replace(konnect_gateway_control_plane.insurance.config.telemetry_endpoint, "https://", "")}:443
    KONNECT_TP_SERVER_NAME=${replace(konnect_gateway_control_plane.insurance.config.telemetry_endpoint, "https://", "")}
  EOT
}
