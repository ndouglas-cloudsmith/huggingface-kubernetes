import os
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd

# Configuration
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
TARGET_ORG = "acme-corporation"

# The list of models you want to migrate
SOURCE_REPOS = [
    "HuggingFaceTB/SmolVLM-256M-Instruct",
    "microsoft/DialoGPT-small",
    "nvidia/esm2_t12_35M_UR50D"
]

api = HfApi()

for repo in SOURCE_REPOS:
    # Extract the short name (e.g., 'DialoGPT-small') for the target repo path
    model_short_name = repo.split("/")[-1]
    print(f"\n--- Processing: {model_short_name} ---")

    try:
        # 1. Download README
        print(f"Downloading README.md from {repo}...")
        card_path = hf_hub_download(repo_id=repo, filename="README.md", endpoint="https://huggingface.co")

        # 2. Identify and Download Model Weights
        # We try safetensors first, then fallback to .bin
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
        print(f"Pushing to Cloudsmith: {TARGET_ORG}/{model_short_name}...")
        api.create_commit(
            repo_id=f"{TARGET_ORG}/{model_short_name}",
            operations=operations,
            commit_message=f"Migrated {model_short_name} from Hugging Face",
            repo_type="model"
        )
        print(f"Successfully migrated {model_short_name}!")

    except Exception as e:
        print(f"Failed to migrate {repo}: {e}")

print("\nAll migrations complete.")
