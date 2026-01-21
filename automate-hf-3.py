import os
import re
import sys
import subprocess
from datetime import datetime

# --- 1. SELF-INSTALL / DEPENDENCY CHECK ---
# This block ensures the libraries are available to whatever Python is running this script
def ensure_dependencies():
    dependencies = ['picklescan', 'huggingface_hub']
    for lib in dependencies:
        try:
            if lib == 'picklescan':
                from picklescan.scanner import Scanner
            else:
                import huggingface_hub
        except ImportError:
            print(f"📦 Missing {lib}. Installing now...")
            # This command tells the CURRENT python to install the library for itself
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib, "--break-system-packages"])

ensure_dependencies()

# Now we can import freely
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd
from huggingface_hub.repocard import ModelCard
try:
    from picklescan.scanner import Scanner
except ImportError:
    # Handle the picklescan internal structure shift
    import picklescan.scanner as pscan
    Scanner = pscan.Scanner

# --- 2. ANSI COLORS & CONFIG ---
BLUE, ORANGE, RED, GREEN, RESET, BOLD = "\033[94m", "\033[93m", "\033[91m", "\033[92m", "\033[0m", "\033[1m"

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

# --- 3. HELPER FUNCTIONS ---
def len_visible(text):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

def scan_pickle_url(url):
    try:
        scanner = Scanner()
        result = scanner.scan_url(url)
        if len(result.issues) == 0:
            return f"{GREEN}Clean{RESET}", True
        return f"{RED}Infected({len(result.issues)}){RESET}", False
    except Exception:
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

# --- 4. MAIN PROCESS ---
try:
    for repo in SOURCE_REPOS:
        model_short_name = repo.split("/")[-1]
        print(f"\n{BOLD}--- Processing: {model_short_name} ---{RESET}")
        scan_summary = f"{GREEN}Clean{RESET}"

        try:
            files_to_migrate, secured, size_mb, license_str = get_repo_files_and_info(repo)
            operations = []
            
            for filename in files_to_migrate:
                if filename.endswith((".bin", ".pt", ".ckpt")):
                    url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
                    status_text, is_safe = scan_pickle_url(url)
                    scan_summary = status_text
                    
                    if not is_safe and "Infected" in status_text:
                        print(f"⚠️  {RED}DANGER: {status_text}{RESET}")
                        confirm = input(f"{ORANGE}Skip this repo for safety? (y/n): {RESET}")
                        if confirm.lower() == 'y': raise Exception("Security Skip")

                print(f"Fetching: {BLUE}{filename:<40}{RESET}")
                file_path = hf_hub_download(repo_id=repo, filename=filename)
                
                if filename.lower() == "readme.md":
                    try:
                        card = ModelCard.load(file_path)
                    except Exception:
                        with open(file_path, "r", encoding="utf-8") as f:
                            card = ModelCard(content=f.read())
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
            
            if os.path.exists(f"temp_readme_{model_short_name}.md"):
                os.remove(f"temp_readme_{model_short_name}.md")

            migration_results.append((model_short_name, license_str, scan_summary, "✅ Success", len(files_to_migrate), size_mb/1024))

        except Exception as e:
            status_msg = "⏭️ Skipped (Security)" if "Security" in str(e) else f"{RED}❌ Failed{RESET}"
            migration_results.append((model_short_name, license_str, scan_summary, status_msg, 0, 0))

except KeyboardInterrupt:
    print(f"\n{ORANGE}🛑 Interrupted.{RESET}")

# --- 5. REPORT ---
print("\n" + "="*95)
print(f"{BOLD}{'MODEL':<35} | {'SCAN':<20} | {'STATUS':<20} | {'SIZE (GB)':<10}{RESET}")
print("-" * 95)
for name, lic, scan, status, files, size in migration_results:
    scan_pad = " " * (20 - len_visible(scan))
    status_pad = " " * (20 - len_visible(status))
    print(f"{name:<35} | {scan}{scan_pad} | {status}{status_pad} | {size:.2f}")
print("="*95)
