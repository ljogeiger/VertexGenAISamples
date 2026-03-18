#!/bin/bash

# ==============================================================================
# Script to Remove Inactive Gemini Enterprise User Licenses
# ==============================================================================

# Default values
PARENT="${1:-projects/sandbox-aiml/locations/global/userStores/default_user_store}" # e.g., projects/123/locations/global/userStores/default_user_store
DAYS="${2:-60}"

if [ -z "$PARENT" ]; then
  echo "Usage: $0 <parent_resource> [days]"
  echo "Example: $0 projects/my-project/locations/global/userStores/default_user_store 60"
  exit 1
fi

gcloud auth application-default set-quota-project sandbox-aiml

# Extract Project ID from PARENT resource for quota billing
QUOTA_PROJECT=$(echo "$PARENT" | cut -d'/' -f2)

# Obtain access token
TOKEN=$(gcloud auth application-default print-access-token 2>/dev/null)
if [ $? -ne 0 ]; then
  echo "Error: Failed to get access token. Please run 'gcloud auth login'."
  exit 1
fi

# Calculate cutoff time as an ISO 8601 UTC string (Z-normalized)
if date --version >/dev/null 2>&1; then
    # GNU date
    CUTOFF_DATE=$(date -u -d "${DAYS} days ago" +"%Y-%m-%dT%H:%M:%SZ")
else
    # BSD/macOS date
    CUTOFF_DATE=$(date -u -v-${DAYS}d +"%Y-%m-%dT%H:%M:%SZ")
fi

echo "Fetching user licenses for $PARENT"
echo "Cutoff date for removal: $CUTOFF_DATE (${DAYS} days ago)"

PAGE_TOKEN=""
INACTIVE_USERS=()

while true; do
  if [ -z "$PAGE_TOKEN" ]; then
    URL="https://discoveryengine.googleapis.com/v1/${PARENT}/userLicenses"
  else
    URL="https://discoveryengine.googleapis.com/v1/${PARENT}/userLicenses?pageToken=${PAGE_TOKEN}"
  fi

  RESPONSE=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Goog-User-Project: $QUOTA_PROJECT" \
    -H "Content-Type: application/json" \
    "$URL")

  # Check if response contains an error
  ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // empty')
  if [ -n "$ERROR_MSG" ]; then
    echo "API Error: $ERROR_MSG"
    exit 1
  fi

  # Parse users who have a lastLoginTime older than the cutoff
  # Since Google APIs return Z-normalized ISO 8601 dates, we can use string comparison in jq
  NEW_INACTIVE=$(echo "$RESPONSE" | jq -r --arg cutoff "$CUTOFF_DATE" '
    .userLicenses[]? |
    select(.lastLoginTime != null and .lastLoginTime != "") |
    select(.lastLoginTime < $cutoff) |
    .name // .userPrincipal
  ')

  for user in $NEW_INACTIVE; do
    if [ -n "$user" ]; then
      INACTIVE_USERS+=("$user")
    fi
  done

  PAGE_TOKEN=$(echo "$RESPONSE" | jq -r '.nextPageToken // empty')
  if [ -z "$PAGE_TOKEN" ]; then
    break
  fi
done

if [ ${#INACTIVE_USERS[@]} -eq 0 ]; then
  echo "No active users found with lastLoginTime > $DAYS days."
  exit 0
fi

echo "Found ${#INACTIVE_USERS[@]} inactive users to remove. Preparing batch update..."

# Prepare the batch request payload dynamically for InlineSource
PAYLOAD_FILE=$(mktemp)
echo '{"deleteUnassignedUserLicenses": true, "inlineSource": {"userLicenses": [' > "$PAYLOAD_FILE"

FIRST=true
for user_identifier in "${INACTIVE_USERS[@]}"; do
  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo ',' >> "$PAYLOAD_FILE"
  fi

  if [[ "$user_identifier" == projects/* ]]; then
    jq -n --arg name "$user_identifier" '{"name": $name, "licenseAssignmentState": "UNASSIGNED"}' >> "$PAYLOAD_FILE"
  else
    jq -n --arg principal "$user_identifier" '{"userPrincipal": $principal, "licenseAssignmentState": "UNASSIGNED"}' >> "$PAYLOAD_FILE"
  fi
done

echo ']}}' >> "$PAYLOAD_FILE"

echo "Executing batchUpdateUserLicenses to set ${#INACTIVE_USERS[@]} users to UNASSIGNED and delete them..."
UPDATE_URL="https://discoveryengine.googleapis.com/v1/${PARENT}:batchUpdateUserLicenses"
UPDATE_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Goog-User-Project: $QUOTA_PROJECT" \
  -H "Content-Type: application/json" \
  -d @"$PAYLOAD_FILE" \
  "$UPDATE_URL")

rm "$PAYLOAD_FILE"

OP_NAME=$(echo "$UPDATE_RESPONSE" | jq -r '.name // empty')

if [ -n "$OP_NAME" ]; then
  echo "Batch update started successfully."
  echo "Operation: $OP_NAME"
else
  echo "Unexpected response or error:"
  echo "$UPDATE_RESPONSE" | jq .
fi
