# VPC・サブネット・セキュリティグループ。
# コスト最小化のため NAT Gateway は使わず、タスクはパブリックサブネットに配置し
# パブリックIPを付与して ECR/Konnect へアウトバウンドする(SGで受信を制限)。

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${local.name}-vpc" }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${local.name}-igw" }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = { Name = "${local.name}-public-${count.index}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = { Name = "${local.name}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# --- Security Groups ---

# ALB: インターネットから 80 を受ける。
resource "aws_security_group" "alb" {
  name        = "${local.name}-alb"
  description = "ALB ingress (HTTP)"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name}-alb" }
}

# Kong DP: ALB からプロキシポート(8000)を受け、アウトバウンドは全許可
# (Konnect CP へ 443、バックエンドへ 8000)。
resource "aws_security_group" "kong_dp" {
  name        = "${local.name}-kong-dp"
  description = "Kong DP proxy"
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "proxy from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name}-kong-dp" }
}

# バックエンド: Kong DP からアプリポート(8000)を受ける。Service Connect の
# サイドカー間通信のため自己参照も許可。アウトバウンドは ECR 取得等のため全許可。
resource "aws_security_group" "backend" {
  name        = "${local.name}-backend"
  description = "FastAPI backend services"
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "app port from Kong DP"
    from_port       = local.container_port
    to_port         = local.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.kong_dp.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name}-backend" }
}

# Service Connect のサイドカー間通信を許可するための自己参照ルール。
resource "aws_security_group_rule" "backend_self" {
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  security_group_id = aws_security_group.backend.id
  self              = true
  description       = "Service Connect sidecar mesh"
}

# Kong DP から Service Connect 経由でバックエンドへ到達できるよう、
# backend SG は kong_dp SG からの全ポートも許可(Service Connect の動的ポート対策)。
resource "aws_security_group_rule" "backend_from_dp_all" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "tcp"
  security_group_id        = aws_security_group.backend.id
  source_security_group_id = aws_security_group.kong_dp.id
  description              = "Service Connect from Kong DP"
}
