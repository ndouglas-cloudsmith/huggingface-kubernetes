import os
import re
import sys
from datetime import datetime
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd
from huggingface_hub.repocard import ModelCard

# Try to import picklescan; if not found, we'll provide a helpful error
try:
    from picklescan.scanner import Scanner
except ImportError:
    print("\033[91mError: 'picklescan' library not found.\033[0m")
    print("Run: pip3 install picklescan huggingface_hub --break-system-packages")
    sys.exit(1)

# --- ANSI Colors ---
BLUE, ORANGE, RED, GREEN, RESET, BOLD = "\033[94m", "\033[93m", "\033[91m", "\033[92m", "\033[0m", "\033[1m"

# --- Configuration ---
public_api = HfApi(endpoint="https://huggingface.co")
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
target_api = HfApi()

TARGET_ORG = "acme-corporation"
CUSTOM_TAGS = ["huggingface"] 
SIZE_THRESHOLD_MB = 500 

SOURCE_REPOS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "prajjwal1/bert-tiny",
    "sshleifer/tiny-distilbert-base-cased-distilled-squad"
]

migration_results = []

def len_visible(text):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

def scan_pickle_url(url):
    """Scans remote URL. Returns (Status_String, Is_Safe)"""
    scanner = Scanner()
    try:
        result = scanner.scan_url(url)
        if len(result.issues) == 0:
            return f"{GREEN}Clean{RESET}", True
        return f"{RED}Infected({len(result.issues)}){RESET}", False
    except Exception as e:
        # Catching the 'unknown opcode' or connection errors
        return f"{ORANGE}Scan Error{RESET}", False

def get_repo_files_and_info(repo_id):
    info = public_api.model_info(repo_id, files_metadata=True)
    all_files = info.siblings
    raw_license = "unknown"
    if hasattr(info, 'card_data') and info.card_data:
        raw_license = info.card_data.get("license", "unknown")
    license_str = ", ".join(raw_license) if isinstance(raw_license, list) else str(raw_license)
    has_safetensors = any(f.rfilename.endswith(".safetensors") for f in all_files)
    
    files_to_download = []
    total_size_bytes = 0
    essential_metadata = ["README.md", "config.json", "tokenizer.json", "tokenizer_config.json"]
    weight_extensions = (".safetensors", ".bin", ".pt", ".h5", ".ckpt")
    
    for f in all_files:
        name = f.rfilename
        is_essential = name.lower() in [m.lower() for m in essential_metadata]
        is_weight = name.endswith(weight_extensions) or ".bin.index.json" in name
        if is_essential or is_weight:
            if has_safetensors and name.endswith((".bin", ".pt", ".ckpt")):
                continue
            files_to_download.append(name)
            if f.size is not None:
                total_size_bytes += f.size
    return list(set(files_to_download)), has_safetensors, (total_size_bytes / (1024 * 1024)), license_str

# --- MAIN LOOP ---
try:
    for repo in SOURCE_REPOS:
        model_short_name = repo.split("/")[-1]
        print(f"\n{BOLD}--- Processing: {model_short_name} ---{RESET}")
        scan_summary = f"{GREEN}Clean{RESET}"

        try:
            files_to_migrate, secured, size_mb, license_str = get_repo_files_and_info(repo)
            
            operations = []
            for filename in files_to_migrate:
                # SCAN RISKY FILES
                if filename.endswith((".bin", ".pt", ".ckpt")):
                    url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
                    status_text, is_safe = scan_pickle_url(url)
                    scan_summary = status_text
                    
                    if not is_safe:
                        print(f"⚠️  {filename}: {status_text}")
                        if "Infected" in status_text:
                            confirm = input(f"{RED}DANGER: Malicious code detected. Skip this model? (y/n): {RESET}")
                            if confirm.lower() == 'y': raise Exception("Security Skip")

                print(f"Fetching: {BLUE}{filename:<40}{RESET}")
                file_path = hf_hub_download(repo_id=repo, filename=filename)
                
                # Update Tags in README
                if filename.lower() == "readme.md":
                    try:
                        card = ModelCard.load(file_path)
                    except:
                        with open(file_path, "r") as f: card = ModelCard(content=f.read())
                    card.data.tags = list(set((card.data.get("tags", []) or []) + CUSTOM_TAGS))
                    temp_readme = f"temp_readme_{model_short_name}.md"
                    card.save(temp_readme)
                    file_path = temp_readme

                operations.append(CommitOperationAdd(path_in_repo=filename, path_or_fileobj=file_path))

            target_api.create_commit(
                repo_id=f"{TARGET_ORG}/{model_short_name}",
                operations=operations,
                commit_message=f"Migrated {model_short_name}",
                repo_type="model"
            )
            migration_results.append((model_short_name, license_str, scan_summary, "✅ Success", len(files_to_migrate), size_mb/1024))

        except Exception as e:
            msg = "⏭️ Skipped (Security)" if "Security" in str(e) else f"{RED}❌ Failed{RESET}"
            migration_results.append((model_short_name, "N/A", scan_summary, msg, 0, 0))

except KeyboardInterrupt:
    print(f"\n{ORANGE}🛑 Interrupted.{RESET}")

# --- REPORT SECTION ---
print(f"\n{BOLD}{'MODEL':<35} | {'SCAN':<20} | {'STATUS':<15} | {'SIZE (GB)':<10}{RESET}")
print("-" * 90)
for name, lic, scan, status, files, size in migration_results:
    print(f"{name:<35} | {scan:<20} | {status:<15} | {size:.2f}")
