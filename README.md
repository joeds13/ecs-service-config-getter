ecs-service-config-getter
===

Pulls configuration files for services running on AWS ECS

## How it works

Uses ENV vars to locate a desired config file, pulls the configuration down to a shared mounted volume. The desired service container awaits the completion, then starts up with its required configs read from the same shared volume.

## Usage

Requires necessary IAM permissions to pull from configuration file source.

Example terraform service definition:

```
resource "aws_ecs_task_definition" "service" {
  family                   = "service"
  requires_compatibilities = ["FARGATE"]
  cpu                      = local.service_cpu
  memory                   = local.service_memory
  network_mode             = "awsvpc"
  task_role_arn            = aws_iam_role.service.arn
  execution_role_arn       = aws_iam_role.service.arn

  volume {
    name = "configs"
  }

  container_definitions = <<JSON
[
  {
    "command": [
      "--config.file=/configs/service.yml"
    ],
    "cpu": ${local.service_cpu - 128},
    "dependsOn": [
        {
            "containerName": "ecs-service-config-getter",
            "condition": "SUCCESS"
        }
    ],
    "essential": true,
    "image": "prom/service:${local.service_version}",
    "logConfiguration": {
      "logDriver": "awslogs",
      "secretOptions": null,
      "options": {
        "awslogs-group": "${aws_cloudwatch_log_group.service.name}",
        "awslogs-region": "eu-west-2",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "memory": ${local.service_memory - 128},
    "mountPoints": [
      {
        "sourceVolume": "configs",
        "containerPath": "/configs"
      }
    ],
    "name": "service",
    "portMappings": [
      {
        "hostPort": ${local.service_port},
        "protocol": "tcp",
        "containerPort": ${local.service_port}
      }
    ]
  },
  {
    "cpu": 128,
    "environment": [
      {
        "name": "CONFIG_PS_ALERTMANAGER_YML",
        "value": "/monitoring/${local.name}/service_yml|/configs/service.yml"
      },
      {
        "name": "CONFIG_PS_NOTIFICATIONS_TMPL",
        "value": "/monitoring/${local.name}/notifications_tmpl|/configs/notifications.tmpl"
      }
    ],
    "essential": false,
    "image": "joeds13/ecs-service-config-getter:1.0.0",
    "logConfiguration": {
      "logDriver": "awslogs",
      "secretOptions": null,
      "options": {
        "awslogs-group": "${aws_cloudwatch_log_group.service.name}",
        "awslogs-region": "eu-west-2",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "memory": 128,
    "mountPoints": [
      {
        "sourceVolume": "configs",
        "containerPath": "/configs"
      }
    ],
    "name": "ecs-service-config-getter"
  }
]
JSON

  tags = {
    Name         = "service"
    source       = "terraform"
    environment  = var.environment
  }
}
```
