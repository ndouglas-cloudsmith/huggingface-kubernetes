import torch
from safetensors.torch import save_file, load_file
import os

# 1. THE DATA
# Unlike Pickle, safetensors ONLY accepts dictionaries of tensors.
# You cannot pass it a class instance with a __reduce__ method.
tensors = {
    "weight_matrix": torch.randn(3, 3),
    "bias": torch.zeros(3)
}

# 2. SAVING (Secure by design)
# This saves the raw bytes. It does not save "how" to create them, 
# just what they "are".
save_file(tensors, "model.safetensors")
print("[+] Tensors saved to 'model.safetensors'")

# 3. LOADING
# When we load, the library only reads the header and maps the bytes.
try:
    loaded_data = load_file("model.safetensors")
    print("[+] Tensors loaded successfully!")
    print(f"Weight Matrix shape: {loaded_data['weight_matrix'].shape}")
except Exception as e:
    print(f"[-] Loading failed: {e}")

# 4. WHY IT'S SAFE
# If an attacker tried to inject 'os.system' into this file, 
# the loader would simply crash because it is looking for 
# specific data types (float32, int64, etc.), not Python opcodes.
