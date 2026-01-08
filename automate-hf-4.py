import os
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd

# 1. Setup API clients
# Use a token if you have one, though these models are public/ungated
public_api = HfApi(endpoint="https://huggingface.co")

# Setting up your target Cloudsmith endpoint
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
target_api = HfApi()

TARGET_ORG = "acme-corporation"

# UPDATED: Small, ungated models with different licenses for testing
SOURCE_REPOS = [
    "sentence-transformers/all-MiniLM-L6-v2",    # Apache 2.0
    "prajjwal1/bert-tiny",                       # MIT
    "nvidia/nemotron-speech-streaming-en-0.6b",  # Other
]

migration_results = []

def get_weight_filename(repo_id):
    """Checks the repo to see which weight file exists."""
    files = public_api.list_repo_files(repo_id)
    if "model.safetensors" in files:
        return "model.safetensors"
    if "pytorch_model.bin" in files:
        return "pytorch_model.bin"
    if "tf_model.h5" in files:
        return "tf_model.h5"
    return None

for repo in SOURCE_REPOS:
    model_short_name = repo.split("/")[-1]
    license_type = "pending..." 
    print(f"\n--- Processing: {model_short_name} ---")

    try:
        # 1. Fetch Metadata
        info = public_api.model_info(repo)
        raw_license = "unknown"
        
        if hasattr(info, 'card_data') and info.card_data:
            raw_license = info.card_data.get("license", "unknown")
        
        # Convert list to comma-separated string if necessary
        license_type = ", ".join(raw_license) if isinstance(raw_license, list) else str(raw_license)
        print(f"Detected License: {license_type}")

        # 2. Determine and Download Weight File
        weights_filename = get_weight_filename(repo)
        if not weights_filename:
            raise FileNotFoundError(f"No standard weight files found in {repo}")

        print(f"Downloading {weights_filename} and README.md...")
        
        card_path = hf_hub_download(repo_id=repo, filename="README.md")
        model_path = hf_hub_download(repo_id=repo, filename=weights_filename)

        # 3. Push to Cloudsmith
        operations = [
            CommitOperationAdd(path_in_repo=weights_filename, path_or_fileobj=model_path),
            CommitOperationAdd(path_in_repo="README.md", path_or_fileobj=card_path)
        ]

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
    print(f"{name:<35} | {str(lic):<20} | {status}")
print("="*80)
