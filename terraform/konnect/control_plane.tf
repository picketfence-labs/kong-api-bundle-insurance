# Kong Konnect の Control Plane を構築する。
resource "konnect_gateway_control_plane" "insurance" {
  name         = var.control_plane_name
  description  = var.control_plane_description
  cluster_type = "CLUSTER_TYPE_CONTROL_PLANE"
  auth_type    = "pki_client_certs"

  labels = {
    project = "kong-api-bundle-insurance"
    domain  = "insurance"
    managed = "terraform"
  }
}
