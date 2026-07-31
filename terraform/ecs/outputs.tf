output "alb_dns_name" {
  description = "Kong DP プロキシのエンドポイント。http://<この値>/product 等でアクセスする。"
  value       = aws_lb.this.dns_name
}

output "ecr_repository_urls" {
  description = "各サービスの ECR リポジトリ URL。build/push に使う。"
  value       = { for k, r in aws_ecr_repository.svc : k => r.repository_url }
}

output "ecs_cluster_name" {
  description = "ECS クラスタ名。"
  value       = aws_ecs_cluster.this.name
}

output "example_requests" {
  description = "動作確認用のリクエスト例。"
  value       = <<-EOT
    curl http://${aws_lb.this.dns_name}/product/products
    curl "http://${aws_lb.this.dns_name}/customer/customers?limit=3"
    curl -X POST http://${aws_lb.this.dns_name}/simulation/simulations \
      -H 'content-type: application/json' \
      -d '{"product_id":"PRD-002","birth_date":"1990-01-01","sum_insured":3000000}'
  EOT
}
