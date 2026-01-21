import os
import re
import sys
import subprocess
from datetime import datetime

# --- 1. DEPENDENCY CHECK ---
def ensure_dependencies():
    for lib in ['picklescan', 'huggingface_hub']:
        try:
            __import__(lib.replace('-', '_'))
        except ImportError:
            print(f"📦 Installing {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib, "--break-system-packages"])

ensure_dependencies()

# --- 2. IMPORTS ---
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd
from huggingface_hub.repocard import ModelCard

# Resilient Scanner Import
try:
    import picklescan.scanner as pscan
    # Check for uppercase first, then lowercase
    Scanner = getattr(pscan, 'Scanner', getattr(pscan, 'scanner', None))
    if Scanner is None:
        raise ImportError
except ImportError:
    print("\033[91mCould not initialize Scanner.\033[0m")
    sys.exit(1)

# --- 3. CONFIG & HELPERS ---
BLUE, ORANGE, RED, GREEN, RESET, BOLD = "\033[94m", "\033[93m", "\033[91m", "\033[92m", "\033[0m", "\033[1m"

public_api = HfApi(endpoint="https://huggingface.co")
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
target_api = HfApi()

TARGET_ORG = "acme-corporation"
CUSTOM_TAGS = ["huggingface"] 
SOURCE_REPOS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "prajjwal1/bert-tiny",
    "sshleifer/tiny-distilbert-base-cased-distilled-squad"
]

migration_results = []

def len_visible(text):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

def scan_pickle_url(url):
    try:
        scanner = Scanner()
        # Ensure the scanner has a scan_url method (compatibility check)
        scan_func = getattr(scanner, 'scan_url', None)
        if not scan_func:
            return f"{ORANGE}Incompatible Lib{RESET}", False
            
        result = scan_func(url)
        if len(result.issues) == 0:
            return f"{GREEN}Clean{RESET}", True
        return f"{RED}Infected({len(result.issues)}){RESET}", False
    except Exception:
        return f"{ORANGE}Scan Error{RESET}", False

# --- 4. MAIN LOOP ---
try:
    for repo in SOURCE_REPOS:
        model_short_name = repo.split("/")[-1]
        print(f"\n{BOLD}--- Processing: {model_short_name} ---{RESET}")
        scan_summary = f"{GREEN}Clean{RESET}"

        try:
            # Simplified file fetching for this demo
            info = public_api.model_info(repo, files_metadata=True)
            files_to_migrate = [f.rfilename for f in info.siblings if f.rfilename.endswith(('.bin', '.safetensors', 'README.md', '.json'))]
            
            operations = []
            for filename in files_to_migrate:
                if filename.endswith(".bin"):
                    url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
                    status_text, is_safe = scan_pickle_url(url)
                    scan_summary = status_text
                
                file_path = hf_hub_download(repo_id=repo, filename=filename)
                operations.append(CommitOperationAdd(path_in_repo=filename, path_or_fileobj=file_path))

            target_api.create_commit(
                repo_id=f"{TARGET_ORG}/{model_short_name}",
                operations=operations,
                commit_message=f"Migrated {model_short_name}",
                repo_type="model"
            )
            migration_results.append((model_short_name, scan_summary, "✅ Success"))

        except Exception as e:
            migration_results.append((model_short_name, scan_summary, f"❌ Failed: {str(e)[:20]}"))

except KeyboardInterrupt:
    print(f"\n{ORANGE}🛑 Interrupted.{RESET}")

# --- 5. REPORT ---
print(f"\n{BOLD}{'MODEL':<35} | {'SCAN':<20} | {'STATUS':<20}{RESET}")
print("-" * 80)
for name, scan, status in migration_results:
    print(f"{name:<35} | {scan:<20} | {status:<20}")
