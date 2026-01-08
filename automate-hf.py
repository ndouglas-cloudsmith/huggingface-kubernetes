import os
import shutil
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd

# No need to set os.environ["HF_TOKEN"] here if it's already exported in your shell.
# However, you still need the Endpoint to point to Cloudsmith!
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"

NEW_NAME = "nigelGPT"
SOURCE_REPO = "HuggingFaceTB/SmolVLM-256M-Instruct"
SOURCE_FILE = "model.safetensors"

api = HfApi()

print(f"Downloading from {SOURCE_REPO}...")
temp_model_path = hf_hub_download(repo_id=SOURCE_REPO, filename=SOURCE_FILE, endpoint="https://huggingface.co")
temp_card_path = hf_hub_download(repo_id=SOURCE_REPO, filename="README.md", endpoint="https://huggingface.co")

# Prepare local renamed copies
local_model_rename = f"{NEW_NAME}.safetensors"
local_card_rename = "README.md"
shutil.copy(temp_model_path, local_model_rename)
shutil.copy(temp_card_path, local_card_rename)

print(f"Pushing to Cloudsmith as {NEW_NAME}...")
operations = [
    CommitOperationAdd(path_in_repo=f"{NEW_NAME}.safetensors", path_or_fileobj=local_model_rename),
    CommitOperationAdd(path_in_repo="README.md", path_or_fileobj=local_card_rename)
]

try:
    api.create_commit(
        repo_id=f"acme-corporation/{NEW_NAME}",
        operations=operations,
        commit_message=f"Upload {NEW_NAME} using shell HF_TOKEN",
        repo_type="model"
    )
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
