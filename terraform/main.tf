# Project Aegis - Main Terraform Configuration
# This configuration deploys the autonomous cost optimization engine

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Aegis"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "target_workload_tags" {
  description = "Tags to identify target workloads for optimization"
  type        = list(string)
  default     = ["environment:production"]
}

variable "optimization_mode" {
  description = "Risk tolerance level (conservative, balanced, aggressive)"
  type        = string
  default     = "balanced"
  
  validation {
    condition     = contains(["conservative", "balanced", "aggressive"], var.optimization_mode)
    error_message = "optimization_mode must be one of: conservative, balanced, aggressive"
  }
}

variable "enable_rightsizing" {
  description = "Enable Layer 1: Proactive & Safe Rightsizing"
  type        = bool
  default     = true
}

variable "enable_graviton_migration" {
  description = "Enable Layer 2: Graviton-Powered Architecture Shift"
  type        = bool
  default     = true
}

variable "enable_spot_orchestration" {
  description = "Enable Layer 3: Intelligent Spot Instance Orchestration"
  type        = bool
  default     = true
}

variable "enable_anomaly_detection" {
  description = "Enable Layer 4: Autonomous Anomaly Detection & Remediation"
  type        = bool
  default     = true
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  sensitive   = true
  default     = ""
}

variable "alert_email" {
  description = "Email address for cost anomaly alerts"
  type        = string
  default     = ""
}

# DynamoDB table for state management and runbooks
resource "aws_dynamodb_table" "aegis_state" {
  name           = "aegis-optimization-state"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "resource_id"
  range_key      = "timestamp"
  
  attribute {
    name = "resource_id"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "N"
  }
  
  ttl {
    attribute_name = "expiration"
    enabled        = true
  }
}

# SNS topic for alerts
resource "aws_sns_topic" "aegis_alerts" {
  name = "aegis-cost-alerts"
}

resource "aws_sns_topic_subscription" "email_alerts" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.aegis_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# IAM role for Lambda functions
resource "aws_iam_role" "aegis_lambda" {
  name = "aegis-lambda-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.aegis_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Discovery Engine Lambda
resource "aws_lambda_function" "discovery_engine" {
  count         = var.enable_rightsizing ? 1 : 0
  filename      = "../src/discovery_engine/lambda_function.zip"
  function_name = "aegis-discovery-engine"
  role          = aws_iam_role.aegis_lambda.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  
  environment {
    variables = {
      OPTIMIZATION_MODE = var.optimization_mode
      STATE_TABLE       = aws_dynamodb_table.aegis_state.name
      SNS_TOPIC_ARN     = aws_sns_topic.aegis_alerts.arn
    }
  }
}

# CloudWatch Event Rule for scheduled discovery
resource "aws_cloudwatch_event_rule" "discovery_schedule" {
  count               = var.enable_rightsizing ? 1 : 0
  name                = "aegis-discovery-schedule"
  description         = "Trigger Aegis discovery engine daily"
  schedule_expression = "rate(1 day)"
}

resource "aws_cloudwatch_event_target" "discovery_lambda" {
  count     = var.enable_rightsizing ? 1 : 0
  rule      = aws_cloudwatch_event_rule.discovery_schedule[0].name
  target_id = "AegisDiscoveryEngine"
  arn       = aws_lambda_function.discovery_engine[0].arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  count         = var.enable_rightsizing ? 1 : 0
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.discovery_engine[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.discovery_schedule[0].arn
}

# Cost Anomaly Detection
resource "aws_ce_anomaly_monitor" "aegis_monitor" {
  count             = var.enable_anomaly_detection ? 1 : 0
  name              = "aegis-cost-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}

resource "aws_ce_anomaly_subscription" "aegis_subscription" {
  count     = var.enable_anomaly_detection ? 1 : 0
  name      = "aegis-anomaly-subscription"
  frequency = "IMMEDIATE"
  
  monitor_arn_list = [
    aws_ce_anomaly_monitor.aegis_monitor[0].arn
  ]
  
  subscriber {
    type    = "SNS"
    address = aws_sns_topic.aegis_alerts.arn
  }
  
  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      values        = ["100"]
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }
}

# Outputs
output "discovery_lambda_arn" {
  description = "ARN of the discovery engine Lambda function"
  value       = var.enable_rightsizing ? aws_lambda_function.discovery_engine[0].arn : null
}

output "state_table_name" {
  description = "Name of the DynamoDB state table"
  value       = aws_dynamodb_table.aegis_state.name
}

output "alerts_topic_arn" {
  description = "ARN of the SNS alerts topic"
  value       = aws_sns_topic.aegis_alerts.arn
}

output "anomaly_monitor_arn" {
  description = "ARN of the cost anomaly monitor"
  value       = var.enable_anomaly_detection ? aws_ce_anomaly_monitor.aegis_monitor[0].arn : null
}
