# AWS adapter IAM permissions

The AWS mode is intentionally narrow and dry-run by default. Grant only the ECS and CloudWatch permissions needed for the checkout deployment-regression scenario.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadCheckoutEvidence",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "logs:FilterLogEvents",
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:DescribeTasks",
        "ecs:ListTasks"
      ],
      "Resource": "*"
    },
    {
      "Sid": "OperateCheckoutService",
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService"
      ],
      "Resource": "arn:aws:ecs:*:*:service/*/checkout-service"
    }
  ]
}
```

Keep `EXECUTE_ACTION_DRY_RUN=true` and `AWS_ACTION_DRY_RUN=true` until the target cluster, service, approval controls, and post-action verification have been validated.
