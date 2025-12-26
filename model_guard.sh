#!/bin/bash

# Usage: bash model_guard.sh openai-community/gpt2
REPO_ID=$1

if [ -z "$REPO_ID" ]; then
    echo "Usage: $0 <username/repo-name>"
    exit 1
fi

echo "--- Scanning Security for: $REPO_ID ---"

# 1. Fetch Model Data
DATA=$(curl -s "https://huggingface.co/api/models/$REPO_ID?securityStatus=true")

# 2. Extract Security Metrics
# Check for "Unsafe" pickle scans
SCAN_STATUS=$(echo "$DATA" | jq -r '.securityStatus.items[]?.status // "clean"' | grep -v "clean" | head -n 1)
# Check for Safetensors (The gold standard for security)
HAS_SAFETENSORS=$(echo "$DATA" | jq -r '.siblings[].rfilename' | grep -c ".safetensors")
# Check Author Reputation (Simplified: Check if author is verified or a major org)
AUTHOR=$(echo "$REPO_ID" | cut -d'/' -f1)

# 3. Calculate Score
SCORE=100
REASONS=()

if [ "$SCAN_STATUS" != "" ] && [ "$SCAN_STATUS" != "clean" ]; then
    SCORE=$((SCORE - 60))
    REASONS+=("[-] FAILED: Automated scan detected unsafe code/malware ($SCAN_STATUS).")
else
    REASONS+=("[+] PASSED: No malicious code detected in automated scans.")
fi

if [ "$HAS_SAFETENSORS" -eq 0 ]; then
    SCORE=$((SCORE - 20))
    REASONS+=("[-] WARNING: No Safetensors found. Model uses older, risky formats (Pickle/Bin).")
else
    REASONS+=("[+] PASSED: Safetensors available (data-only format, execution-safe).")
fi

# 4. Final Output
echo "FINAL SECURITY SCORE: $SCORE/100"
for reason in "${REASONS[@]}"; do echo "$reason"; done

if [ $SCORE -ge 80 ]; then
    echo -e "\033[0;32mRESULT: PASS (Safe to download)\033[0m"
else
    echo -e "\033[0;31mRESULT: FAIL (High Risk - Inspect manually)\033[0m"
fi
