from huggingface_hub import upload_folder
import os

# Ensure these are set in your environment or set them here:
os.environ["HF_ENDPOINT"] = "https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one"
os.environ["HF_TOKEN"] = "your-api-key"

upload_folder(
    folder_path="./my-local-model-folder",  # The folder containing your .gguf file
    repo_id="acme-corporation/qwen-0.5b",   # How it will appear in Cloudsmith
    repo_type="model",
    commit_message="Uploading Qwen model to Cloudsmith"
)
