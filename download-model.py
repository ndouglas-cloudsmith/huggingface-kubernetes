from huggingface_hub import hf_hub_download

# This ignores your HF_ENDPOINT and goes to the real Hugging Face
file_path = hf_hub_download(
    repo_id="bartowski/Qwen2.5-0.5B-Instruct-GGUF",
    filename="Qwen2.5-0.5B-Instruct-Q4_K_M.gguf",
    endpoint="https://huggingface.co" # Force the public hub
)
