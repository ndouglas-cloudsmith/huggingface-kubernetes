from huggingface_hub import upload_file, hf_hub_download
import os

# Your Cloudsmith config
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
os.environ["HF_TOKEN"] = "your-cloudsmith-api-key"

# 1. Get the local path of the file you already downloaded
local_file_path = hf_hub_download(
    repo_id="bartowski/Qwen2.5-0.5B-Instruct-GGUF",
    filename="Qwen2.5-0.5B-Instruct-Q4_K_M.gguf",
    endpoint="https://huggingface.co" # Use real HF to find the local path
)

# 2. Upload that specific file to Cloudsmith
upload_file(
    path_or_fileobj=local_file_path,
    path_in_repo="Qwen2.5-0.5B-Instruct-Q4_K_M.gguf",
    repo_id="acme-corporation/qwen-0.5b",
    repo_type="model",
    commit_message="Uploading specific GGUF file to Cloudsmith"
)

print("Upload successful!")
