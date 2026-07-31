# Kong DP プロキシの前段に置く Application Load Balancer。
# クライアントは ALB の DNS 名経由で各サービスへアクセスする。

resource "aws_lb" "this" {
  name               = "${local.name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "kong_dp" {
  name        = "${local.name}-kong-dp"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.this.id
  target_type = "ip"

  health_check {
    path = "/"
    # ルート未マッチ時 Kong は 404 を返すため、404 も正常とみなして DP の生存を確認する。
    matcher  = "200,404"
    interval = 30
    timeout  = 5
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.kong_dp.arn
  }
}
