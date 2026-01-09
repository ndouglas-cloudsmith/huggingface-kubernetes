import os
import re
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd

# ANSI Color Codes
BLUE = "\033[94m"
ORANGE = "\033[93m"  # Bright yellow/orange
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Configuration
public_api = HfApi(endpoint="https://huggingface.co")
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
target_api = HfApi()

TARGET_ORG = "acme-corporation"
SOURCE_REPOS = [
    "sentence-transformers/all-MiniLM-L6-v2",            # apache-2.0
    "prajjwal1/bert-tiny",                               # mit 
    "govtech/lionguard-2",                               # other
    "bs-la/bloomz-7b1-500m-ru",                          # bigscience-bloom-rail-1.0
    "song9/embeddinggemma-300m-KorSTS",                  # cc-by-sa-4.0
    "nqzfaizal77ai/solstice-pulse-pt-gpt2-100m",         # openrail
    "aphexblake/200-msf-v2",                             # creativeml-openrail-m
    "facebook/mms-300m",                                 # cc-by-nc-4.0
#   "hal2k/llama2-7b-chat-sae-layer14-16x-pile-100m",,
#   "elRivx/100Memories",,
#   "nikitastheo/BERTtime-Stories-100m-nucleus-1",
#   "SkyOrbis/SKY-Ko-Llama3.2-1B-lora-epoch3",
#   "h2oai/h2o-danube3-500m-chat",
#   "microsoft/bitnet_b1_58-large",
#   "stabilityai/stablelm-2-1_6b",
#   "google/gemma-2b",
#   "unsloth/Llama-3.2-1B",
]

migration_results = []

def len_visible(text):
    """Calculates the visible length of a string, ignoring ANSI escape sequences."""
    return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

def get_color_license(license_str):
    """Returns the license string wrapped in the appropriate ANSI color."""
    l_lower = license_str.lower()
    if "mit" in l_lower or "apache-2.0" in l_lower:
        return f"{ORANGE}{license_str}{RESET}"
    return f"{RED}{license_str}{RESET}"

def get_repo_files_to_migrate(repo_id):
    all_files = public_api.list_repo_files(repo_id)
    files_to_download = []

    essential_metadata = [
        "README.md", "config.json", "generation_config.json", 
        "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
        "vocab.txt", "merges.txt", "added_tokens.json"
    ]
    for meta_file in essential_metadata:
        if meta_file in all_files:
            files_to_download.append(meta_file)

    if "model.safetensors.index.json" in all_files:
        files_to_download.append("model.safetensors.index.json")
        shards = [f for f in all_files if "model-00" in f and f.endswith(".safetensors")]
        files_to_download.extend(shards)
    elif "pytorch_model.bin.index.json" in all_files:
        files_to_download.append("pytorch_model.bin.index.json")
        shards = [f for f in all_files if "pytorch_model-00" in f and f.endswith(".bin")]
        files_to_download.extend(shards)
    else:
        weight_extensions = (".safetensors", ".bin", ".pt", ".h5", ".ckpt")
        weights = [f for f in all_files if f.endswith(weight_extensions) and f not in files_to_download]
        files_to_download.extend(weights)
            
    return list(set(files_to_download))

for repo in SOURCE_REPOS:
    model_short_name = repo.split("/")[-1]
    print(f"\n{BOLD}--- Processing: {model_short_name} ---{RESET}")

    try:
        info = public_api.model_info(repo)
        raw_license = "unknown"
        if hasattr(info, 'card_data') and info.card_data:
            raw_license = info.card_data.get("license", "unknown")
        
        license_str = ", ".join(raw_license) if isinstance(raw_license, list) else str(raw_license)
        colored_license = get_color_license(license_str)
        print(f"Detected License: {colored_license}")

        files_to_migrate = get_repo_files_to_migrate(repo)
        
        has_weights = any(f.endswith((".safetensors", ".bin", ".pt", ".h5", ".ckpt")) for f in files_to_migrate)
        if not has_weights:
            print(f"{RED}⚠️ Warning: No weight files found. Migrating metadata only.{RESET}")

        if not files_to_migrate:
            raise FileNotFoundError(f"No files found at all in {repo}")

        print(f"Downloading {len(files_to_migrate)} files...")
        operations = []
        for filename in files_to_migrate:
            print(f"Fetching: {BLUE}{filename}{RESET}")
            file_path = hf_hub_download(repo_id=repo, filename=filename)
            operations.append(CommitOperationAdd(path_in_repo=filename, path_or_fileobj=file_path))

        target_api.create_commit(
            repo_id=f"{TARGET_ORG}/{model_short_name}",
            operations=operations,
            commit_message=f"Migrated {model_short_name} | License: {license_str}",
            repo_type="model"
        )
        
        status = "✅ Success" if has_weights else "⚠️ Success (No Weights)"
        migration_results.append((model_short_name, colored_license, status))
        print(f"Status: {status}")

    except Exception as e:
        status = f"{RED}❌ Failed (Error){RESET}"
        if "409" in str(e): status = "⚠️ Skipped (Exists)"
        print(f"Status: {status} - {e}")
        migration_results.append((model_short_name, RED + "Error" + RESET, status))

# --- FINAL REPORT ---
# Widths: Model=35, License=35, Status=20 (Total ~95 including separators)
MODEL_COL_WIDTH = 35
LICENSE_COL_WIDTH = 35

print("\n" + "=" * 95)
print(f"{BOLD}{'MODEL':<35} | {'LICENSE':<35} | {'STATUS'}{RESET}")
print("-" * 95)

for name, lic, status in migration_results:
    # Manual padding to account for invisible ANSI characters
    name_pad = " " * (MODEL_COL_WIDTH - len_visible(name))
    lic_pad = " " * (LICENSE_COL_WIDTH - len_visible(lic))
    
    print(f"{name}{name_pad} | {lic}{lic_pad} | {status}")

print("=" * 95)
