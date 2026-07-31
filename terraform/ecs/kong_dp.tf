# Kong Gateway (Data Plane) を ECS 上で hybrid mode で起動し、Konnect の
# Control Plane に接続する。DP のクライアント証明書・鍵は Konnect スタックが
# 生成したものを Secrets Manager に格納し、コンテナ起動時にファイルへ書き出す。

resource "aws_secretsmanager_secret" "dp_cert" {
  name                    = "${local.name}/kong-dp/tls-crt"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "dp_cert" {
  secret_id     = aws_secretsmanager_secret.dp_cert.id
  secret_string = file(var.dp_cert_path)
}

resource "aws_secretsmanager_secret" "dp_key" {
  name                    = "${local.name}/kong-dp/tls-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "dp_key" {
  secret_id     = aws_secretsmanager_secret.dp_key.id
  secret_string = file(var.dp_key_path)
}

resource "aws_ecs_task_definition" "kong_dp" {
  family                   = "${local.name}-kong-dp"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.kong_cpu
  memory                   = var.kong_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "kong-dp"
      image     = "kong/kong-gateway:3.15"
      essential = true

      # Secrets(PEM文字列)は環境変数 CLUSTER_CERT/CLUSTER_KEY に注入し、
      # entrypoint でファイルへ書き出してから Kong を起動する。
      entryPoint = ["/bin/sh", "-c"]
      command = [
        "printf '%s' \"$CLUSTER_CERT\" > /tmp/tls.crt && printf '%s' \"$CLUSTER_KEY\" > /tmp/tls.key && /docker-entrypoint.sh kong docker-start"
      ]

      portMappings = [
        { containerPort = 8000, protocol = "tcp" },
        { containerPort = 8443, protocol = "tcp" },
      ]

      environment = [
        { name = "KONG_ROLE", value = "data_plane" },
        { name = "KONG_DATABASE", value = "off" },
        { name = "KONG_VITALS", value = "off" },
        { name = "KONG_CLUSTER_MTLS", value = "pki" },
        { name = "KONG_KONNECT_MODE", value = "on" },
        { name = "KONG_CLUSTER_CONTROL_PLANE", value = "${local.cp_host}:443" },
        { name = "KONG_CLUSTER_SERVER_NAME", value = local.cp_host },
        { name = "KONG_CLUSTER_TELEMETRY_ENDPOINT", value = "${local.tp_host}:443" },
        { name = "KONG_CLUSTER_TELEMETRY_SERVER_NAME", value = local.tp_host },
        { name = "KONG_CLUSTER_CERT", value = "/tmp/tls.crt" },
        { name = "KONG_CLUSTER_CERT_KEY", value = "/tmp/tls.key" },
        { name = "KONG_LUA_SSL_TRUSTED_CERTIFICATE", value = "system" },
        { name = "KONG_PROXY_ACCESS_LOG", value = "/dev/stdout" },
        { name = "KONG_PROXY_ERROR_LOG", value = "/dev/stderr" },
      ]

      secrets = [
        { name = "CLUSTER_CERT", valueFrom = aws_secretsmanager_secret.dp_cert.arn },
        { name = "CLUSTER_KEY", valueFrom = aws_secretsmanager_secret.dp_key.arn },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.kong_dp.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "kong_dp" {
  name            = "kong-dp"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.kong_dp.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.kong_dp.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.kong_dp.arn
    container_name   = "kong-dp"
    container_port   = 8000
  }

  # Service Connect の「クライアント」として参加し、バックエンドを
  # discovery name(product 等)で解決できるようにする。
  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_http_namespace.this.arn
  }

  depends_on = [
    aws_lb_listener.http,
    aws_ecs_service.svc,
    aws_ecs_cluster_capacity_providers.this,
  ]
}
