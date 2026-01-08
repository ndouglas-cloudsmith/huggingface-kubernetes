import os
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd

# 1. Setup the two different API clients
# public_api is for reading from Hugging Face
public_api = HfApi(endpoint="https://huggingface.co")

# target_api is for writing to Cloudsmith
# We use the full URL to ensure it ignores any global environment variables
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
target_api = HfApi()

TARGET_ORG = "acme-corporation"

SOURCE_REPOS = [
    "HuggingFaceTB/SmolVLM-256M-Instruct", # Apache 2.0 (~500MB)
    "microsoft/DialoGPT-small",            # MIT (~350MB)
    "nvidia/esm2_t12_35M_UR50D",           # MIT/Custom (~130MB)
    "PrunaAI/gpt2-tiny-opt",               # OpenRAIL (~45MB)
    "squeezebert/squeezebert-uncased"      # BSD 3-Clause (~100MB)
]

for repo in SOURCE_REPOS:
    model_short_name = repo.split("/")[-1]
    print(f"\n--- Processing: {model_short_name} ---")

    try:
        # 1. Fetch Metadata from Public HF
        print(f"Fetching metadata for {repo}...")
        info = public_api.model_info(repo)
        
        license_type = "unknown"
        if hasattr(info, 'card_data') and info.card_data is not None:
            license_type = info.card_data.get("license", "unknown")
        
        print(f"Detected License: {license_type}")

        # 2. Download files from Public HF
        print(f"Downloading README.md...")
        card_path = hf_hub_download(repo_id=repo, filename="README.md", endpoint="https://huggingface.co")

        weights_filename = "model.safetensors"
        try:
            print(f"Downloading {weights_filename}...")
            model_path = hf_hub_download(repo_id=repo, filename=weights_filename, endpoint="https://huggingface.co")
        except Exception:
            weights_filename = "pytorch_model.bin"
            print(f"Safetensors not found. Falling back to {weights_filename}...")
            model_path = hf_hub_download(repo_id=repo, filename=weights_filename, endpoint="https://huggingface.co")

        # 3. Prepare Push Operations
        operations = [
            CommitOperationAdd(path_in_repo=weights_filename, path_or_fileobj=model_path),
            CommitOperationAdd(path_in_repo="README.md", path_or_fileobj=card_path)
        ]

        # 4. Push to Cloudsmith
        # The license is added to the commit message which helps Cloudsmith's indexing
        commit_msg = f"Migrated {model_short_name} | License: {license_type}"
        
        print(f"Pushing to Cloudsmith: {TARGET_ORG}/{model_short_name}...")
        target_api.create_commit(
            repo_id=f"{TARGET_ORG}/{model_short_name}",
            operations=operations,
            commit_message=commit_msg,
            repo_type="model"
        )
        print(f"Successfully migrated {model_short_name} with license tag: {license_type}!")

    except Exception as e:
        print(f"Failed to migrate {repo}: {e}")

print("\nAll migrations complete.")
