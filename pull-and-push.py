from huggingface_hub import snapshot_download, upload_folder
import os

# 1. Download ONLY the Model Card and the specific GGUF file
local_dir = snapshot_download(
    repo_id="bartowski/Qwen2.5-0.5B-Instruct-GGUF",
    endpoint="https://huggingface.co",
    # This filter is the magic part:
    allow_patterns=["README.md", "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"]
)

# 2. Configure for Cloudsmith
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
os.environ["HF_TOKEN"] = "your-cloudsmith-api-key"

# 3. Upload the filtered folder
# Now it only sends 2 files to Cloudsmith instead of 25!
upload_folder(
    folder_path=local_dir,
    repo_id="acme-corporation/qwen-0.5b",
    repo_type="model",
    commit_message="Uploading Q4_K_M model and its model card"
)

print("Upload successful! Only the necessary files were pushed.")
