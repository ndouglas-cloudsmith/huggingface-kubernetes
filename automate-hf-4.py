import os
import re
from datetime import datetime
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd
from huggingface_hub.repocard import ModelCard

# ANSI Color Codes
BLUE = "\033[94m"
ORANGE = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"
BOLD = "\033[1m"

# File Purpose Dictionary
FILE_PURPOSES = {
    "README.md": "Documentation and model card metadata.",
    "config.json": "Model architecture configuration (the 'skeleton').",
    "tokenizer.json": "The vocabulary and rules for converting text to numbers.",
    "tokenizer_config.json": "Settings for the text preprocessing pipeline.",
    "special_tokens_map.json": "Mapping for tokens like [CLS], [SEP], or <|endoftext|>.",
    "vocab.txt": "Plain text list of the model's vocabulary.",
    "merges.txt": "Subword merging rules for byte-pair encoding.",
    "added_tokens.json": "Custom tokens added to the base vocabulary.",
    "model.safetensors": "Model weights in a secure, non-executable format.",
    "pytorch_model.bin": "Model weights in PyTorch format (Legacy/Risky).",
    "tf_model.h5": "Model weights in TensorFlow/Keras format.",
    "model.ckpt": "Training checkpoint containing weights.",
    "generation_config.json": "Parameters for controlling text generation.",
}

# Configuration
public_api = HfApi(endpoint="https://huggingface.co")
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
target_api = HfApi()

TARGET_ORG = "acme-corporation"
CUSTOM_TAGS = ["huggingface"] 
SIZE_THRESHOLD_MB = 500 

SOURCE_REPOS = [
    "ykilcher/totally-harmless-model",                   # N/A
    "sentence-transformers/all-MiniLM-L6-v2",            # apache-2.0
    "prajjwal1/bert-tiny",                               # mit 
    "govtech/lionguard-2",                               # other
    "nikitastheo/BERTtime-Stories-100m-nucleus-1",       # gpl-3.0    
    "bs-la/bloomz-7b1-500m-ru",                          # bigscience-bloom-rail-1.0
    "nqzfaizal77ai/solstice-pulse-pt-gpt2-100m",         # openrail
    "aphexblake/200-msf-v2",                             # creativeml-openrail-m
    "h2oai/h2o-danube3-500m-chat",                       # apache-2.0    
    "facebook/mms-300m",                                 # cc-by-nc-4.0
    "unsloth/Llama-3.2-1B",                              # llama3.2
    "hal2k/llama2-7b-chat-sae-layer14-16x-pile-100m",    # cc-by-sa-4.0
    "SkyOrbis/SKY-Ko-Llama3.2-1B-lora-epoch3",           # llama3
#   "song9/embeddinggemma-300m-KorSTS",                  # cc-by-sa-4.0    
#   "elRivx/100Memories",                                # creativeml-openrail-m
#   "microsoft/VibeVoice-Realtime-0.5B",                 # mit
#   "stabilityai/stablelm-2-1_6b",                       # other
#   "google/functiongemma-270m-it",                      # gemma
#   "nvidia/parakeet-tdt-0.6b-v3",                       # cc-by-4.0 
]

migration_results = []

def len_visible(text):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

def get_color_license(license_str):
    l_lower = license_str.lower()
    if "mit" in l_lower or "apache-2.0" in l_lower:
        return f"{ORANGE}{license_str}{RESET}"
    return f"{RED}{license_str}{RESET}"

def get_file_description(filename):
    if filename in FILE_PURPOSES: return FILE_PURPOSES[filename]
    if filename.endswith(".safetensors"): return FILE_PURPOSES["model.safetensors"]
    if filename.endswith(".bin"): return FILE_PURPOSES["pytorch_model.bin"]
    return "Supporting configuration or model file."

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
    essential_metadata = ["README.md", "config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "vocab.txt", "merges.txt", "added_tokens.json"]
    weight_extensions = (".safetensors", ".bin", ".pt", ".h5", ".ckpt")
    
    for f in all_files:
        name = f.rfilename
        is_essential = name.lower() in [m.lower() for m in essential_metadata]
        is_weight = name.endswith(weight_extensions) or ".bin.index.json" in name or ".safetensors.index.json" in name
        
        if is_essential or is_weight:
            if has_safetensors and name.endswith((".bin", ".pt", ".ckpt")):
                continue
            files_to_download.append(name)
            if f.size is not None:
                total_size_bytes += f.size
            
    return list(set(files_to_download)), has_safetensors, (total_size_bytes / (1024 * 1024)), license_str

# Start the migration process with an interrupt handler
try:
    for repo in SOURCE_REPOS:
        model_short_name = repo.split("/")[-1]
        print(f"\n{BOLD}--- Processing: {model_short_name} ---{RESET}")

        try:
            files_to_migrate, secured, size_mb, license_str = get_repo_files_and_info(repo)
            colored_license = get_color_license(license_str)
            num_files = len(files_to_migrate)
            size_gb = size_mb / 1024
            
            sec_msg = f"{GREEN}🛡️  Secure (Safetensors){RESET}" if secured else f"{RED}🚨 Risky (Legacy .bin){RESET}"
            print(f"License: {colored_license}")
            print(f"Scan: {sec_msg} | Total Size: {BOLD}{size_mb:.2f} MB ({size_gb:.2f} GB){RESET}")

            if size_mb > SIZE_THRESHOLD_MB:
                confirm = input(f"{ORANGE}⚠️ Large Model detected. Continue? (y/n): {RESET}")
                if confirm.lower() != 'y':
                    migration_results.append((model_short_name, colored_license, "⏭️  Skipped..", num_files, size_gb))
                    continue

            print(f"Downloading {num_files} files...")
            operations = []
            for filename in files_to_migrate:
                print(f"Fetching: {BLUE}{filename:<40}{RESET} | {get_file_description(filename)}")
                file_path = hf_hub_download(repo_id=repo, filename=filename)
                
                if filename.lower() == "readme.md":
                    try:
                        card = ModelCard.load(file_path)
                    except Exception:
                        with open(file_path, "r", encoding="utf-8") as f:
                            existing_content = f.read()
                        card = ModelCard(content=existing_content)
                    
                    existing_tags = card.data.get("tags", []) or []
                    if isinstance(existing_tags, str): existing_tags = [existing_tags]
                    card.data.tags = list(set(existing_tags + CUSTOM_TAGS))
                    if license_str != "unknown":
                        card.data.license = license_str
                    
                    temp_readme = f"temp_readme_{model_short_name}.md"
                    card.save(temp_readme)
                    file_path = temp_readme

                operations.append(CommitOperationAdd(path_in_repo=filename, path_or_fileobj=file_path))

            target_api.create_commit(
                repo_id=f"{TARGET_ORG}/{model_short_name}",
                operations=operations,
                commit_message=f"Migrated {model_short_name} | Tags: {', '.join(CUSTOM_TAGS)}",
                repo_type="model"
            )
            
            if os.path.exists(f"temp_readme_{model_short_name}.md"):
                os.remove(f"temp_readme_{model_short_name}.md")

            migration_results.append((model_short_name, colored_license, "✅ Success", num_files, size_gb))

        except Exception as e:
            status = "⚠️  Skipped (Exists)" if "409" in str(e) else f"{RED}❌ Failed{RESET}"
            migration_results.append((model_short_name, RED + "Error" + RESET, status, 0, 0))

except KeyboardInterrupt:
    print(f"\n\n{ORANGE}🛑 Interrupted by user. Skipping remaining models and jumping to report...{RESET}")

# --- FINAL REPORT ---
M_COL, L_COL, S_COL, F_COL, Z_COL = 45, 25, 18, 10, 12
TOTAL_WIDTH = M_COL + L_COL + S_COL + F_COL + Z_COL + 12
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("\n" + "=" * TOTAL_WIDTH)
print(f"{BOLD}MIGRATION REPORT | {current_time}{RESET}")
print("-" * TOTAL_WIDTH)
print(f"{BOLD}{'MODEL':<{M_COL}} | {'LICENSE':<{L_COL}} | {'STATUS':<{S_COL}} | {'FILES':<{F_COL}} | {'SIZE (GB)':<{Z_COL}}{RESET}")
print("-" * TOTAL_WIDTH)

total_session_files = 0
total_session_gb = 0

for name, lic, status, files, size in migration_results:
    name_pad = " " * (M_COL - len_visible(name))
    lic_pad = " " * (L_COL - len_visible(lic))
    status_pad = " " * (S_COL - len_visible(status))
    
    # Rounded to 2 decimal places for cleaner visual
    size_str = f"{size:.2f}"
    print(f"{name}{name_pad} | {lic}{lic_pad} | {status}{status_pad} | {files:<{F_COL}} | {size_str:<{Z_COL}}")
    
    if "Success" in status:
        total_session_files += files
        total_session_gb += size

print("-" * TOTAL_WIDTH)
# Total label is slightly shorter to align with columns
total_label = "GRAND TOTAL (SUCCESSFUL MIGRATIONS)"
print(f"{BOLD}{total_label:<{M_COL + L_COL + S_COL + 6}} | {total_session_files:<{F_COL}} | {total_session_gb:.2f}{RESET}")
print("=" * TOTAL_WIDTH)
