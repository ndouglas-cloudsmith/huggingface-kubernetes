from huggingface_hub import snapshot_download, upload_folder
import os

# 1. Download the FULL repository from public HF
# This includes the .gguf AND the README.md (the model card)
local_dir = snapshot_download(
    repo_id="bartowski/Qwen2.5-0.5B-Instruct-GGUF",
    endpoint="https://huggingface.co",
    # Optional: if the repo is huge, you can filter to just the GGUF and README
    allow_patterns=["*.gguf", "README.md"] 
)

# 2. Configure for Cloudsmith
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
os.environ["HF_TOKEN"] = "your-cloudsmith-api-key"

# 3. Upload the entire folder
upload_folder(
    folder_path=local_dir,
    repo_id="acme-corporation/qwen-0.5b",
    repo_type="model",
    commit_message="Uploading full model snapshot including model card"
)

print("Upload complete: Model and Card should now be visible!")
