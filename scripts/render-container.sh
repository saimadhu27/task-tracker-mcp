#!/usr/bin/env bash
# Print the service's container settings (deploy/primary-container.json.tmpl) with the
# placeholders filled in from environment variables.
#
#   IMAGE=... PUBLIC_BASE_URL=https://... AWS_REGION=... ACCOUNT_ID=... scripts/render-container.sh
set -euo pipefail

: "${IMAGE:?IMAGE is not set}"
: "${PUBLIC_BASE_URL:?PUBLIC_BASE_URL is not set}"
: "${AWS_REGION:?AWS_REGION is not set}"
: "${ACCOUNT_ID:?ACCOUNT_ID is not set}"

PUBLIC_BASE_URL="${PUBLIC_BASE_URL%/}" # no trailing slash
case "$PUBLIC_BASE_URL" in
  https://*) ;;
  *) echo "PUBLIC_BASE_URL must start with https:// (got: $PUBLIC_BASE_URL)" >&2; exit 1 ;;
esac

rendered=$(sed \
  -e "s|__IMAGE__|$IMAGE|g" \
  -e "s|__PUBLIC_BASE_URL__|$PUBLIC_BASE_URL|g" \
  -e "s|__AWS_REGION__|$AWS_REGION|g" \
  -e "s|__ACCOUNT_ID__|$ACCOUNT_ID|g" \
  "$(dirname "$0")/../deploy/primary-container.json.tmpl")

if grep -Eq '__[A-Z_]+__' <<<"$rendered"; then
  echo "Some placeholders were not replaced:" >&2
  grep -Eo '__[A-Z_]+__' <<<"$rendered" | sort -u >&2
  exit 1
fi

jq . <<<"$rendered" # also checks that the result is valid JSON