# Kong Data Plane (hybrid mode) 接続用の自己署名証明書を生成し、
# Control Plane に data-plane client certificate として登録する。
# 生成した証明書・鍵はローカル(certs/)に書き出し、docker-compose の DP が参照する。
# generate_dp_certificate = false の場合はこのファイルの全リソースが作成されない。

resource "tls_private_key" "dp" {
  count     = var.generate_dp_certificate ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "tls_self_signed_cert" "dp" {
  count           = var.generate_dp_certificate ? 1 : 0
  private_key_pem = tls_private_key.dp[0].private_key_pem

  subject {
    common_name  = "kong-insurance-dp"
    organization = "kong-api-bundle-insurance"
    country      = "JP"
  }

  validity_period_hours = 26280 # 約3年

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
  ]
}

resource "konnect_gateway_data_plane_client_certificate" "dp" {
  count            = var.generate_dp_certificate ? 1 : 0
  control_plane_id = konnect_gateway_control_plane.insurance.id
  cert             = tls_self_signed_cert.dp[0].cert_pem
}

resource "local_file" "dp_cert" {
  count           = var.generate_dp_certificate ? 1 : 0
  content         = tls_self_signed_cert.dp[0].cert_pem
  filename        = "${path.module}/${var.dp_cert_output_dir}/tls.crt"
  file_permission = "0644"
}

resource "local_sensitive_file" "dp_key" {
  count           = var.generate_dp_certificate ? 1 : 0
  content         = tls_private_key.dp[0].private_key_pem
  filename        = "${path.module}/${var.dp_cert_output_dir}/tls.key"
  file_permission = "0600"
}
