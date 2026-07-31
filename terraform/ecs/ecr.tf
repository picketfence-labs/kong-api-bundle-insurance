# 各サービスのコンテナイメージ格納先(ECRリポジトリ)。
# scripts/build_push_ecr.sh でビルド・push する。

resource "aws_ecr_repository" "svc" {
  for_each = toset(local.services)

  name                 = "${local.name}/${each.key}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# 直近イメージのみ保持するライフサイクルポリシー(コスト対策)。
resource "aws_ecr_lifecycle_policy" "svc" {
  for_each   = aws_ecr_repository.svc
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}
