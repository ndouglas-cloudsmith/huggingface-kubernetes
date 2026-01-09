import os
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd

public_api = HfApi(endpoint="https://huggingface.co")
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
target_api = HfApi()

TARGET_ORG = "acme-corporation"
SOURCE_REPOS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "prajjwal1/bert-tiny",
    "govtech/lionguard-2",
    "h2oai/h2o-danube3-500m-chat",
    "microsoft/bitnet_b1_58-large",
    "stabilityai/stablelm-2-1_6b",
    "google/gemma-2b",
    "unsloth/Llama-3.2-1B",
]

migration_results = []

def get_weight_filenames(repo_id):
    """Returns a list of all weight-related files (shards or single files)."""
    files = public_api.list_repo_files(repo_id)
    
    # Check for sharded safetensors first (Common for Llama 3.1)
    if "model.safetensors.index.json" in files:
        shards = [f for f in files if "model-00" in f and f.endswith(".safetensors")]
        return ["model.safetensors.index.json"] + shards
    
    # Check for single files
    for single_file in ["model.safetensors", "pytorch_model.bin", "tf_model.h5"]:
        if single_file in files:
            return [single_file]
            
    return []

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

        # 2. Get list of files
        weights_list = get_weight_filenames(repo)
        if not weights_list:
            raise FileNotFoundError(f"No standard weight files found in {repo}")

        print(f"Downloading {len(weights_list)} weight file(s) and README.md...")
        
        operations = []
        # Download README
        card_path = hf_hub_download(repo_id=repo, filename="README.md")
        operations.append(CommitOperationAdd(path_in_repo="README.md", path_or_fileobj=card_path))

        # Download all weight files (shards or single)
        for weight_file in weights_list:
            file_path = hf_hub_download(repo_id=repo, filename=weight_file)
            operations.append(CommitOperationAdd(path_in_repo=weight_file, path_or_fileobj=file_path))

        # 3. Push to Cloudsmith
        commit_msg = f"Migrated {model_short_name} | License: {license_type}"
        target_api.create_commit(
            repo_id=f"{TARGET_ORG}/{model_short_name}",
            operations=operations,
            commit_message=commit_msg,
            repo_type="model"
        )
        migration_results.append((model_short_name, license_type, "✅ Success"))
        print(f"Status: ✅ Successfully migrated to {TARGET_ORG}/{model_short_name}")

    except Exception as e:
        status = "❌ Failed (Error)"
        if "409" in str(e): 
            status = "⚠️ Skipped (Exists)"
        print(f"Status: {status} - {e}")
        migration_results.append((model_short_name, license_type, status))

# --- FINAL REPORT ---
print("\n" + "="*80)
print(f"{'MODEL':<35} | {'LICENSE':<20} | {'STATUS'}")
print("-" * 80)
for name, lic, status in migration_results:
    print(f"{name:<35} | {str(lic)[:20]:<20} | {status}")
print("="*80)
