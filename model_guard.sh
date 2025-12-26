#!/bin/bash

# Usage: bash model_guard.sh <repo_id> [local_file_to_verify]
REPO_ID=$1
LOCAL_FILE=$2

if [ -z "$REPO_ID" ]; then
    echo "Usage: $0 <username/repo-name> [local_file_path]"
    exit 1
fi

echo "--- 🛡️  Scanning Security for: $REPO_ID ---"

# 1. Fetch Model Metadata
DATA=$(curl -s "https://huggingface.co/api/models/$REPO_ID?securityStatus=true")

# 2. Extract Security Metrics
# Check for any security items that are NOT "clean"
UNSAFE_HITS=$(echo "$DATA" | jq -r '.securityStatus.items[]? | select(.status != "clean") | .status' | wc -l | xargs)
# Identify if the scan is actually present or "null/unknown"
HAS_SCAN_DATA=$(echo "$DATA" | jq -r '.securityStatus.items' | grep -v "null" | wc -l | xargs)

# Check for Safetensors (Modern, safe format)
HAS_SAFETENSORS=$(echo "$DATA" | jq -r '.siblings[].rfilename' | grep -c ".safetensors")

# 3. Security Scoring Logic
SCORE=100
REASONS=()

# Criterion A: Automated Malware/Pickle Scan
if [ "$UNSAFE_HITS" -gt 0 ]; then
    SCORE=$((SCORE - 80))
    REASONS+=("[-] CRITICAL: Automated scan detected MALICIOUS or UNSAFE code.")
elif [ "$HAS_SCAN_DATA" -eq 0 ] && [ "$HAS_SAFETENSORS" -eq 0 ]; then
    SCORE=$((SCORE - 50))
    REASONS+=("[-] WARNING: No scan data available for legacy format. Possible obfuscation.")
else
    REASONS+=("[+] PASSED: No malicious patterns detected in automated scans.")
fi

# Criterion B: Format Safety
if [ "$HAS_SAFETENSORS" -eq 0 ]; then
    SCORE=$((SCORE - 20))
    REASONS+=("[-] WARNING: Missing Safetensors. Using execution-prone formats (Pickle/Bin).")
else
    REASONS+=("[+] PASSED: Safetensors present (Safe-by-design format).")
fi

# 4. Optional: File Integrity Check (SHA256)
if [ -f "$LOCAL_FILE" ]; then
    echo "--- 🔍 Verifying File Integrity: $(basename "$LOCAL_FILE") ---"
    
    # Get remote hash from API (matching filename)
    FILENAME=$(basename "$LOCAL_FILE")
    REMOTE_HASH=$(echo "$DATA" | jq -r --arg fname "$FILENAME" '.siblings[] | select(.rfilename == $fname) | .lfs.oid' | cut -d':' -f2)
    
    # Calculate local hash (Works on macOS and Linux)
    if command -v shasum &> /dev/null; then
        LOCAL_HASH=$(shasum -a 256 "$LOCAL_FILE" | awk '{print $1}')
    else
        LOCAL_HASH=$(sha256sum "$LOCAL_FILE" | awk '{print $1}')
    fi

    if [ "$REMOTE_HASH" == "null" ] || [ -z "$REMOTE_HASH" ]; then
        REASONS+=("[-] INTEGRITY: Could not find hash for $FILENAME in HF metadata.")
    elif [ "$LOCAL_HASH" == "$REMOTE_HASH" ]; then
        REASONS+=("[+] INTEGRITY: Local SHA256 matches Hugging Face record.")
    else
        SCORE=$((SCORE - 100))
        REASONS+=("[-] CRITICAL: HASH MISMATCH! Local file does not match official record.")
    fi
fi

# 5. Final Report
echo "---------------------------------------"
echo "FINAL SECURITY SCORE: $SCORE/100"
for reason in "${REASONS[@]}"; do echo "$reason"; done

if [ $SCORE -ge 80 ]; then
    echo -e "\033[0;32mRESULT: PASS\033[0m"
else
    echo -e "\033[0;31mRESULT: FAIL - High Risk\033[0m"
fi
