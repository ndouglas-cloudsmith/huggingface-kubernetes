import os
import re
import subprocess
from datetime import datetime
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd
from huggingface_hub.repocard import ModelCard

# --- 1. CONFIG & STYLING ---
BLUE, ORANGE, RED, GREEN, RESET, BOLD = "\033[94m", "\033[93m", "\033[91m", "\033[92m", "\033[0m", "\033[1m"

FILE_PURPOSES = {
    "README.md": "Documentation and model card metadata.",
    "config.json": "Model architecture configuration (the 'skeleton').",
    "tokenizer.json": "The vocabulary and rules for converting text to numbers.",
    "model.safetensors": "Model weights in a secure, non-executable format.",
    "pytorch_model.bin": "Model weights in PyTorch format (Legacy/Risky).",
}

public_api = HfApi(endpoint="https://huggingface.co")
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
target_api = HfApi()

TARGET_ORG = "acme-corporation"
CUSTOM_TAGS = ["huggingface"] 
SIZE_THRESHOLD_MB = 500 

SOURCE_REPOS = [
    "ykilcher/totally-harmless-model", # Added for testing your scanner
    "sentence-transformers/all-MiniLM-L6-v2",
    "prajjwal1/bert-tiny",
    "govtech/lionguard-2",
    "nikitastheo/BERTtime-Stories-100m-nucleus-1",
    "bs-la/bloomz-7b1-500m-ru",
    "nqzfaizal77ai/solstice-pulse-pt-gpt2-100m"
]

# --- 2. HELPER FUNCTIONS ---

def len_visible(text):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

def get_color_license(license_str):
    l_lower = license_str.lower()
    if "mit" in l_lower or "apache-2.0" in l_lower:
        return f"{ORANGE}{license_str}{RESET}"
    return f"{RED}{license_str}{RESET}"

def scan_huggingface_repo(repo_id):
    """Uses the CLI directly to avoid initialization overengineering."""
    try:
        result = subprocess.run(
            ['picklescan', '--huggingface', repo_id], 
            capture_output=True, 
            text=True
        )
        if "dangerous import" in result.stdout:
            return f"{RED}Infected{RESET}", False
        return f"{GREEN}Clean{RESET}", True
    except FileNotFoundError:
        return f"{ORANGE}picklescan not found{RESET}", False
    except Exception as e:
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
    essential_metadata = ["README.md", "config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json"]
    weight_extensions = (".safetensors", ".bin", ".pt", ".h5", ".ckpt")
    
    for f in all_files:
        name = f.rfilename
        is_essential = name.lower() in [m.lower() for m in essential_metadata]
        is_weight = name.endswith(weight_extensions) or ".index.json" in name
        
        if is_essential or is_weight:
            # If safetensors exist, skip the risky bin files
            if has_safetensors and name.endswith((".bin", ".pt", ".ckpt")):
                continue
            files_to_download.append(name)
            if f.size is not None:
                total_size_bytes += f.size
            
    return list(set(files_to_download)), has_safetensors, (total_size_bytes / (1024 * 1024)), license_str

# --- 3. MAIN PROCESS ---

migration_results = []

try:
    for repo in SOURCE_REPOS:
        model_short_name = repo.split("/")[-1]
        print(f"\n{BOLD}--- Processing: {model_short_name} ---{RESET}")

        # A. Security Scan (CLI Based)
        scan_label, is_safe = scan_huggingface_repo(repo)
        print(f"Pickle Scan: {scan_label}")
        
        if not is_safe and "Clean" not in scan_label:
            print(f"{RED}🛑 Security Block: Dangerous imports found. Skipping.{RESET}")
            migration_results.append((model_short_name, "N/A", f"{RED}Infected{RESET}", 0, 0))
            continue

        try:
            # B. Metadata Gathering
            files_to_migrate, secured, size_mb, license_str = get_repo_files_and_info(repo)
            colored_license = get_color_license(license_str)
            num_files = len(files_to_migrate)
            size_gb = size_mb / 1024
            
            sec_msg = f"{GREEN}🛡️  Safetensors{RESET}" if secured else f"{RED}🚨 Legacy Bin{RESET}"
            print(f"Format: {sec_msg} | Size: {size_mb:.2f} MB")

            if size_mb > SIZE_THRESHOLD_MB:
                confirm = input(f"{ORANGE}⚠️  Large Model. Continue? (y/n): {RESET}")
                if confirm.lower() != 'y':
                    migration_results.append((model_short_name, colored_license, "⏭️  Skipped", num_files, size_gb))
                    continue

            # C. Download & Prepare Operations
            operations = []
            for filename in files_to_migrate:
                print(f"Fetching: {BLUE}{filename:<30}{RESET}")
                file_path = hf_hub_download(repo_id=repo, filename=filename)
                
                if filename.lower() == "readme.md":
                    try:
                        card = ModelCard.load(file_path)
                    except Exception:
                        with open(file_path, "r", encoding="utf-8") as f:
                            card = ModelCard(content=f.read())
                    
                    # Update Tags
                    tags = card.data.get("tags", []) or []
                    card.data.tags = list(set((tags if isinstance(tags, list) else [tags]) + CUSTOM_TAGS))
                    card.data.license = license_str
                    
                    temp_readme = f"temp_readme_{model_short_name}.md"
                    card.save(temp_readme)
                    file_path = temp_readme

                operations.append(CommitOperationAdd(path_in_repo=filename, path_or_fileobj=file_path))

            # D. Push to Target
            target_api.create_commit(
                repo_id=f"{TARGET_ORG}/{model_short_name}",
                operations=operations,
                commit_message=f"Migrated {model_short_name}",
                repo_type="model"
            )
            
            # Cleanup temp readme
            if os.path.exists(f"temp_readme_{model_short_name}.md"):
                os.remove(f"temp_readme_{model_short_name}.md")

            migration_results.append((model_short_name, colored_license, "✅ Success", num_files, size_gb))

        except Exception as e:
            status = "⚠️  Exists" if "409" in str(e) else f"{RED}❌ Failed{RESET}"
            migration_results.append((model_short_name, "Error", status, 0, 0))

except KeyboardInterrupt:
    print(f"\n{ORANGE}🛑 Interrupted.{RESET}")

# --- 4. FINAL REPORT ---
M_COL, L_COL, S_COL, F_COL, Z_COL = 40, 20, 15, 8, 10
TOTAL_WIDTH = M_COL + L_COL + S_COL + F_COL + Z_COL + 12
print("\n" + "=" * TOTAL_WIDTH)
print(f"{BOLD}{'MODEL':<{M_COL}} | {'LICENSE':<{L_COL}} | {'STATUS':<{S_COL}} | {'FILES':<{F_COL}} | {'GB':<{Z_COL}}{RESET}")
print("-" * TOTAL_WIDTH)

for name, lic, status, files, size in migration_results:
    n_pad = " " * (M_COL - len_visible(name))
    l_pad = " " * (L_COL - len_visible(lic))
    s_pad = " " * (S_COL - len_visible(status))
    print(f"{name}{n_pad} | {lic}{l_pad} | {status}{s_pad} | {files:<{F_COL}} | {size:<.2f}")
print("=" * TOTAL_WIDTH)
