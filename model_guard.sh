#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: bash model_guard.sh <repo1> <repo2> ..."
    exit 1
fi

for REPO_ID in "$@"; do
    echo -e "\n\033[1;34m========================================================\033[0m"
    echo -e "\033[1;34m🛡️  SCANNING REPOSITORY: $REPO_ID\033[0m"
    echo -e "\033[1;34m========================================================\033[0m"

    # 1. Fetch data and verify it is valid JSON
    RESPONSE=$(curl -sL "https://huggingface.co/api/models/$REPO_ID?securityStatus=true")
    
    if ! echo "$RESPONSE" | jq empty > /dev/null 2>&1; then
        echo -e "\033[0;31m[-] ERROR: Could not fetch valid data for $REPO_ID.\033[0m"
        echo "    (Check if the repo name is correct or if it contains special characters like colons)"
        continue
    fi

    # 2. Extract Security Metrics with "Safe Defaults"
    # Logic: If field is missing, jq returns 0 instead of null
    UNSAFE_HITS=$(echo "$RESPONSE" | jq -r '(.securityStatus.items // []) | map(select(.status != "clean")) | length')
    HAS_SCAN_DATA=$(echo "$RESPONSE" | jq -r 'if .securityStatus.items then (.securityStatus.items | length) else 0 end')
    
    # Check for Safetensors OR GGUF (Case-insensitive)
    HAS_SAFE_FORMAT=$(echo "$RESPONSE" | jq -r '.siblings[].rfilename' | grep -Ei -c "\.(safetensors|gguf)$")

    # 3. Security Scoring Logic
    SCORE=100
    REASONS=()

    # Rule 1: Malicious Code detected
    if [ "$UNSAFE_HITS" -gt 0 ]; then
        SCORE=$((SCORE - 80))
        REASONS+=("[-] CRITICAL: Automated scan detected MALICIOUS or UNSAFE code.")
    # Rule 2: Legacy format with NO scan verification (Zero-Trust)
    elif [ "$HAS_SCAN_DATA" -eq 0 ] && [ "$HAS_SAFE_FORMAT" -eq 0 ]; then
        SCORE=$((SCORE - 50))
        REASONS+=("[-] WARNING: No scan data available for legacy format. Possible obfuscation.")
    else
        REASONS+=("[+] PASSED: No malicious patterns detected in automated scans.")
    fi

    # Rule 3: Format Check
    if [ "$HAS_SAFE_FORMAT" -eq 0 ]; then
        SCORE=$((SCORE - 20))
        REASONS+=("[-] WARNING: No Safetensors or GGUF found. Using risky formats (Pickle/Bin).")
    else
        REASONS+=("[+] PASSED: Safe-by-design format found (Safetensors or GGUF).")
    fi

    # 4. Final Output
    echo "FINAL SECURITY SCORE: $SCORE/100"
    for reason in "${REASONS[@]}"; do echo "$reason"; done

    if [ "$SCORE" -ge 80 ]; then
        echo -e "\033[0;32mRESULT for $REPO_ID: PASS\033[0m"
    else
        echo -e "\033[0;31mRESULT for $REPO_ID: FAIL - High Risk\033[0m"
    fi
done
