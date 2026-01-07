from huggingface_hub import snapshot_download, upload_folder
import os
import shutil

# 1. Define a clean local path
local_path = "./model-to-upload"

# OPTIONAL: Clear the folder if it exists to ensure no old files are left over
if os.path.exists(local_path):
    shutil.rmtree(local_path)

# 2. Download ONLY the Model Card and the specific GGUF file into that folder
snapshot_download(
    repo_id="bartowski/Qwen2.5-0.5B-Instruct-GGUF",
    endpoint="https://huggingface.co",
    local_dir=local_path, # Forces files into this specific folder
    allow_patterns=["README.md", "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"]
)

# 3. Configure for Cloudsmith
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
os.environ["HF_TOKEN"] = "your-cloudsmith-api-key"

# 4. Upload ONLY that folder
upload_folder(
    folder_path=local_path,
    repo_id="acme-corporation/qwen-0.5b",
    repo_type="model",
    commit_message="Uploading clean snapshot: Q4_K_M and README only"
)

print("Success! Only the 2 specified files were uploaded.")
