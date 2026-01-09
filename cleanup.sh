#!/bin/bash

API_KEY="${CLOUDSMITH_API_KEY}"
OWNER="acme-corporation"
REPOSITORY="acme-repo-one"

# Define multiple tags in an array
TAGS=("transformer" "feature-extraction" "classifier" "facebook" "causal-lm" "llm" "multilingual")

PAGE_SIZE=250
BASE_URL="https://api.cloudsmith.io/v1/packages/${OWNER}/${REPOSITORY}/"

function delete_tagged_packages() {
    # Accept the tag as an argument to the function
    local CURRENT_TAG=$1
    echo "----------------------------------------------------"
    echo "🔍 Fetching packages with tag '$CURRENT_TAG' from repository '$REPOSITORY'..."
    echo "----------------------------------------------------"

    current_page=1
    packages_deleted=0

    while true; do
        echo "🔄 Processing page $current_page for tag '$CURRENT_TAG'..."

        # Fetch package list
        packages=$(curl -s -H "X-Api-Key: $API_KEY" \
            -G "$BASE_URL" \
            --data-urlencode "query=tag:$CURRENT_TAG" \
            --data-urlencode "page=$current_page" \
            --data-urlencode "page_size=$PAGE_SIZE")

        # Validate that the response is a JSON array
        if ! echo "$packages" | jq -e 'type == "array"' >/dev/null 2>&1; then
            echo "✅ No more packages found with tag '$CURRENT_TAG'."
            break
        fi

        names=($(echo "$packages" | jq -r '.[].name'))
        slugs=($(echo "$packages" | jq -r '.[].slug_perm'))

        if [[ "${#slugs[@]}" -eq 0 ]]; then
            echo "✅ No more packages found with tag '$CURRENT_TAG'."
            break
        fi

        for i in "${!slugs[@]}"; do
            echo "Deleting package ${names[$i]}, ID: ${slugs[$i]}"
            response=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
                -H "X-Api-Key: ${API_KEY}" \
                "${BASE_URL}${slugs[$i]}/")

            if [ "$response" -eq 204 ]; then
                echo "✅ Deleted: ${names[$i]}"
                ((packages_deleted++))
            else
                echo "❌ Failed to delete: ${names[$i]} (Status: $response)"
            fi
        done

        # Note: If you delete packages, Cloudsmith's pagination might shift. 
        # Usually, staying on page 1 is safer for deletions, but since 
        # these are distinct slugs, incrementing page is the standard approach.
        ((current_page++))
    done

    echo "🎉 Total Packages Deleted for '$CURRENT_TAG': $packages_deleted"
}

# Iterate through the array and call the function for each tag
for TAG in "${TAGS[@]}"; do
    delete_tagged_packages "$TAG"
done

echo "🏁 All tags processed."
