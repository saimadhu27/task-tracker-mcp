#!/usr/bin/env bash
# Run a one-off command in the deployed service's container, inside AWS.
#
#   scripts/ecs-run.sh alembic upgrade head
#   scripts/ecs-run.sh python -m task_tracker.admin create-user you@example.com
#   SENSITIVE=1 scripts/ecs-run.sh python -m task_tracker.admin create-key you@example.com --name laptop
#   RUN_IMAGE=<ecr image> scripts/ecs-run.sh alembic upgrade head   # an image that is not deployed yet
#
# SENSITIVE=1 deletes the task's log stream after printing it, for output that contains a secret.
set -euo pipefail

CLUSTER="${ECS_CLUSTER:-default}"
SERVICE="${ECS_SERVICE:-task-tracker}"
[ "$#" -gt 0 ] || { echo "usage: $0 COMMAND [ARGS...]" >&2; exit 2; }

# Reuse the service's own task definition and network settings, so the task gets the same
# secrets and the same security group (the one the database allows in).
svc=$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --query 'services[0]' --output json)
#task_def=$(jq -r '.taskDefinition' <<<"$svc")
express_arn=$(jq -r '.serviceArn' <<<"$svc")
net_cfg=$(aws ecs describe-express-gateway-service --service-arn "$express_arn" \
  --query 'service.activeConfigurations[0].networkConfiguration' --output json)
network=$(jq -c '{awsvpcConfiguration: {subnets, securityGroups, assignPublicIp: "ENABLED"}}' <<<"$net_cfg")
task_def=$(aws ecs describe-express-gateway-service --service-arn "$express_arn" \
  --query 'service.activeConfigurations[0].taskDefinitionArn' --output text)
if [ "$(jq -r '.awsvpcConfiguration.subnets | length' <<<"$network")" -eq 0 ]; then
  echo "Could not read the service's network settings. Is ECS_SERVICE=$SERVICE right?" >&2
  exit 1
fi

td_json=$(aws ecs describe-task-definition --task-definition "$task_def" --query taskDefinition --output json)

# A copy of the task definition that points at a different image (used to migrate before deploying).
if [ -n "${RUN_IMAGE:-}" ]; then
  tmp=$(mktemp)
  jq --arg image "$RUN_IMAGE" \
    'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)
     | .containerDefinitions[0].image = $image' <<<"$td_json" >"$tmp"
  td_json=$(aws ecs register-task-definition --cli-input-json "file://$tmp" --query taskDefinition --output json)
  rm -f "$tmp"
  task_def=$(jq -r '.taskDefinitionArn' <<<"$td_json")
fi

container=$(jq -r '.containerDefinitions[0].name' <<<"$td_json")
log_group=$(jq -r '.containerDefinitions[0].logConfiguration.options["awslogs-group"] // empty' <<<"$td_json")
log_prefix=$(jq -r '.containerDefinitions[0].logConfiguration.options["awslogs-stream-prefix"] // empty' <<<"$td_json")

# Build the command as a JSON array one argument at a time. (Passing "$@" to jq with --args breaks
# when an argument starts with a dash, such as -m or --name.)
command_json='[]'
for arg in "$@"; do
  command_json=$(jq -c --arg a "$arg" '. + [$a]' <<<"$command_json")
done
overrides=$(jq -cn --arg name "$container" --argjson command "$command_json" \
  '{containerOverrides: [{name: $name, command: $command}]}')
task_arn=$(aws ecs run-task --cluster "$CLUSTER" --launch-type FARGATE --task-definition "$task_def" \
  --network-configuration "$network" --overrides "$overrides" \
  --query 'tasks[0].taskArn' --output text)
if [ -z "$task_arn" ] || [ "$task_arn" = "None" ]; then
  echo "ECS could not start the task. Check your IAM permissions and the network settings." >&2
  exit 1
fi
task_id=${task_arn##*/}
echo "Started task $task_id. Waiting for it to finish..."
aws ecs wait tasks-stopped --cluster "$CLUSTER" --tasks "$task_arn"

exit_code=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$task_arn" \
  --query 'tasks[0].containers[0].exitCode' --output text)

if [ -n "$log_group" ]; then
  stream="$log_prefix/$container/$task_id"
  sleep 5 # logs can lag a few seconds behind the task
  echo "----- output -----"
  aws logs get-log-events --log-group-name "$log_group" --log-stream-name "$stream" --output json \
    | jq -r '.events[].message' || true
  echo "------------------"
  if [ "${SENSITIVE:-}" = "1" ]; then
    aws logs delete-log-stream --log-group-name "$log_group" --log-stream-name "$stream" \
      && echo "(log stream deleted)"
  fi
fi

if [ "$exit_code" != "0" ]; then
  reason=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$task_arn" \
    --query 'tasks[0].stoppedReason' --output text)
  echo "The task failed (exit code: $exit_code). Reason: $reason" >&2
  exit 1
fi
echo "The task finished successfully."