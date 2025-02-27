# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "webapp_and_api_user_pool_id" {
  value = var.use_shared_user_pool ? var.webapp_and_api_shared_user_pool_id : aws_cognito_user_pool.webapp_and_api_user_pool[0].id
}

output "webapp_and_api_user_pool_client_id" {
  value = var.use_shared_user_pool ? var.webapp_and_api_shared_user_pool_client_id : aws_cognito_user_pool_client.webapp_and_api_user_pool_client[0].id
}
