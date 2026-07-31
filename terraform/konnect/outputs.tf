output "control_plane_id" {
  description = "作成された Control Plane の ID。Kubernetes の KonnectGatewayControlPlane(Mirror) から参照する。"
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
