import os
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd

# Configuration
public_api = HfApi(endpoint="https://huggingface.co")
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
target_api = HfApi()

TARGET_ORG = "acme-corporation"
SOURCE_REPOS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "prajjwal1/bert-tiny",
    "govtech/lionguard-2",
#   "aphexblake/200-msf-v2",
#   "elRivx/100Memories",
#   "song9/embeddinggemma-300m-KorSTS",
#   "hal2k/llama2-7b-chat-sae-layer14-16x-pile-100m",
    "nqzfaizal77ai/solstice-pulse-pt-gpt2-100m",
#   "facebook/mms-300m",
#   "nikitastheo/BERTtime-Stories-100m-nucleus-1",
#   "SkyOrbis/SKY-Ko-Llama3.2-1B-lora-epoch3",
#   "h2oai/h2o-danube3-500m-chat",
#   "microsoft/bitnet_b1_58-large",
#   "stabilityai/stablelm-2-1_6b",
#   "google/gemma-2b",
#   "unsloth/Llama-3.2-1B",
]

migration_results = []

def get_repo_files_to_migrate(repo_id):
    all_files = public_api.list_repo_files(repo_id)
    files_to_download = []

    # 1. Essential Config & Metadata
    essential_metadata = [
        "README.md", "config.json", "generation_config.json", 
        "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
        "vocab.txt", "merges.txt", "added_tokens.json"
    ]
    for meta_file in essential_metadata:
        if meta_file in all_files:
            files_to_download.append(meta_file)

    # 2. Identify Weight Files
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
    license_type = "pending..." 
    print(f"\n--- Processing: {model_short_name} ---")

    try:
        info = public_api.model_info(repo)
        raw_license = "unknown"
        if hasattr(info, 'card_data') and info.card_data:
            raw_license = info.card_data.get("license", "unknown")
        
        license_type = ", ".join(raw_license) if isinstance(raw_license, list) else str(raw_license)
        print(f"Detected License: {license_type}")

        files_to_migrate = get_repo_files_to_migrate(repo)
        
        # Check if weights are present for logging, but don't stop the script
        has_weights = any(f.endswith((".safetensors", ".bin", ".pt", ".h5", ".ckpt")) for f in files_to_migrate)
        if not has_weights:
            print("⚠️ Warning: No weight files found. Migrating metadata only.")

        if not files_to_migrate:
            raise FileNotFoundError(f"No files found at all in {repo}")

        print(f"Downloading {len(files_to_migrate)} files...")
        operations = []
        for filename in files_to_migrate:
            file_path = hf_hub_download(repo_id=repo, filename=filename)
            operations.append(CommitOperationAdd(path_in_repo=filename, path_or_fileobj=file_path))

        target_api.create_commit(
            repo_id=f"{TARGET_ORG}/{model_short_name}",
            operations=operations,
            commit_message=f"Migrated {model_short_name} | License: {license_type}",
            repo_type="model"
        )
        
        status = "✅ Success" if has_weights else "⚠️ Success (No Weights)"
        migration_results.append((model_short_name, license_type, status))
        print(f"Status: {status}")

    except Exception as e:
        status = "❌ Failed (Error)"
        if "409" in str(e): status = "⚠️ Skipped (Exists)"
        print(f"Status: {status} - {e}")
        migration_results.append((model_short_name, license_type, status))

# --- FINAL REPORT ---
print("\n" + "="*80)
print(f"{'MODEL':<35} | {'LICENSE':<20} | {'STATUS'}")
print("-" * 80)
for name, lic, status in migration_results:
    print(f"{name:<35} | {str(lic)[:20]:<20} | {status}")
print("="*80)
