terraform {
  required_version = ">= 1.5"

  required_providers {
    konnect = {
      source  = "Kong/konnect"
      version = "~> 2.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
