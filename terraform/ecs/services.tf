# 6バックエンドサービスの Task Definition と ECS Service。
# すべて同一構造のため for_each で定義する。イメージはビルド時に data/seed を
# 同梱済みのため、SEED_FILE 等の追加設定は不要。

resource "aws_ecs_task_definition" "svc" {
  for_each = toset(local.services)

  family                   = "${local.name}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = each.key
      image     = "${aws_ecr_repository.svc[each.key].repository_url}:${var.image_tag}"
      essential = true

      portMappings = [
        {
          # Service Connect はこの name を discovery に用いる。
          name          = each.key
          containerPort = local.container_port
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.svc[each.key].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "svc" {
  for_each = toset(local.services)

  name            = each.key
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.svc[each.key].arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = true
  }

  # Service Connect の「サーバー」として自サービスを discovery name で公開する。
  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_http_namespace.this.arn

    service {
      port_name      = each.key
      discovery_name = each.key

      client_alias {
        port     = local.container_port
        dns_name = each.key
      }
    }
  }

  depends_on = [aws_ecs_cluster_capacity_providers.this]
}
