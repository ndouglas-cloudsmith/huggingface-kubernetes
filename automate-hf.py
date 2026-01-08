import os
import shutil
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd

# 1. Cloudsmith Configuration
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
os.environ["HF_TOKEN"] = "your-cloudsmith-api-key"

NEW_NAME = "nigelGPT"
SOURCE_REPO = "HuggingFaceTB/SmolVLM-256M-Instruct"
SOURCE_FILE = "model.safetensors"

api = HfApi()

# 2. Download Files
print(f"Downloading {SOURCE_FILE}...")
temp_model_path = hf_hub_download(repo_id=SOURCE_REPO, filename=SOURCE_FILE, endpoint="https://huggingface.co")

print("Downloading Model Card...")
temp_card_path = hf_hub_download(repo_id=SOURCE_REPO, filename="README.md", endpoint="https://huggingface.co")

# 3. Prepare local renamed copies
local_model_rename = f"{NEW_NAME}.safetensors"
local_card_rename = "README.md"
shutil.copy(temp_model_path, local_model_rename)
shutil.copy(temp_card_path, local_card_rename)

# 4. Push BOTH files in ONE commit
print(f"Pushing {NEW_NAME} to Cloudsmith in a single commit...")

operations = [
    CommitOperationAdd(path_in_repo=f"{NEW_NAME}.safetensors", path_or_fileobj=local_model_rename),
    CommitOperationAdd(path_in_repo="README.md", path_or_fileobj=local_card_rename)
]

try:
    api.create_commit(
        repo_id=f"acme-corporation/{NEW_NAME}",
        operations=operations,
        commit_message=f"Initial upload of {NEW_NAME} with model card",
        repo_type="model"
    )
    print(f"Success! {NEW_NAME} and its model card are now on Cloudsmith.")
except Exception as e:
    print(f"Failed to push: {e}") 
