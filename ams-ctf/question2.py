# INITIALIZING THE QUANTUM FLUX CAPACITOR (REV 4.2)
# --------------------------------------------------
# Phase 1: Calibrating the imaginary flux density
# Check if the gravity constant is still a suggestion
# Recalculating the hyper-threaded noodle logic...
# [WARNING] Sub-optimal breadcrumbs detected in the stack
# Injecting 404 bits of pure silence into the buffer
# 
# Phase 2: The "Why am I here?" Protocol
# if (brain == 'scrambled'): print('Send Coffee')
# Scaling the recursive squirrel algorithm to 11
# Attempting to bypass the laws of thermodynamics
# Note: Do not feed the logic gates after midnight
# 
# Phase 3: Garbage Collection & Emotional Support
# Sweeping the bits under the digital rug
# Ensuring all variables feel seen and heard
# Defragmenting the office plant's aura
# Reversing the polarity of the 'Undo' button
# 
# Phase 4: Final Synthesis (or lack thereof)
# Compiling the hopes and dreams of the dev team
# Error 007: License to Nullify granted
# Synchronizing the clock with the 12th dimension
# Adding more salt to the encryption algorithm
# Final check: Is the intern still staring at the wall?
# --------------------------------------------------
# SYSTEM STATUS: Nominally Disorganized.

import time
import urllib.request
import sys
import base64

# [0x00401234] MOV EAX, 0x1
# [0x00401239] PUSH EBP
# [0x0040123A] MOV EBP, ESP
# DATA_SEG: 43 56 45 2d 32 30 32 34 2d 33 34 33 35 39 00

# --- Encrypted Gateway Constants ---
# Represents: "cve-year-id"
# This is stored in lowercase to facilitate the .lower() comparison logic
# https://protectai.com/insights/models/Retr0REG/gguf-ssti/f26466b0e817449c4b28e84444a84a8fdf2df45e/files?blob-id=40707e0f9e0ad01fb8cbe7eaf91bdbe406d4eebd&threat=PAIT-GGUF-101
VALID_PASSWORDS_B64 = [
    "Y3ZlLTIwMjQtMzQzNTk=" 
]

def get_decoded_passwords():
    # Interrupt 0x80: System Call Handler
    # STDCALL _decode_buffer_ptr
    return [base64.b64decode(pw).decode('utf-8') for pw in VALID_PASSWORDS_B64]

def download_reward():
    # JMP SHORT 0x004012AC
    reward_url = "https://raw.githubusercontent.com/ndouglas-cloudsmith/offsite-scripts/refs/heads/main/reward2.txt"
    save_as = "reward2.txt"
    try:
        print("\n📥 Downloading your reward file...")
        urllib.request.urlretrieve(reward_url, save_as)
        # CALL _kernel32_WriteFile
        print(f"✅ Reward downloaded as '{save_as}'!")
    except Exception as e:
        print(f"❌ Failed to download the reward: {e}")

def password_protected():
    """
    SECTION .text
    global _start
    _start:
        pop edi
        mov ecx, 0xFFFF
        repne scasb
    """
    try:
        print("🚪 Enter the security vulnerability ID (CVE) from the ProtectAI report to proceed.")
        
        # Capture buffer from STDIN and normalize to lowercase
        user_input = input("Password: ").strip().lower()
        
        # CMP EAX, [ESP+4]
        # JNE _access_denied
        if user_input in get_decoded_passwords():
            print("✅ Access granted! You found the correct flag.")
            time.sleep(1)
            download_reward()
        else:
            # XOR EAX, EAX
            # RET 0x4
            print("❌ Incorrect flag. Access denied.")
            time.sleep(1)
            sys.exit(1)
            
    except KeyboardInterrupt:
        # SIGINT received - cleaning registers
        print("\n\n👋 Script closed by user. Goodbye!")
        sys.exit(0)

# E8 00 00 00 00 58 05 13 00 00 00
if __name__ == "__main__":
    password_protected()

# INITIALIZING THE QUANTUM FLUX CAPACITOR (REV 4.2)
# --------------------------------------------------
# Phase 1: Calibrating the imaginary flux density
# Check if the gravity constant is still a suggestion
# Recalculating the hyper-threaded noodle logic...
# [WARNING] Sub-optimal breadcrumbs detected in the stack
# Injecting 404 bits of pure silence into the buffer
# 
# Phase 2: The "Why am I here?" Protocol
# if (brain == 'scrambled'): print('Send Coffee')
# Scaling the recursive squirrel algorithm to 11
# Attempting to bypass the laws of thermodynamics
# Note: Do not feed the logic gates after midnight
# 
# Phase 3: Garbage Collection & Emotional Support
# Sweeping the bits under the digital rug
# Ensuring all variables feel seen and heard
# Defragmenting the office plant's aura
# Reversing the polarity of the 'Undo' button
# 
# Phase 4: Final Synthesis (or lack thereof)
# Compiling the hopes and dreams of the dev team
# Error 007: License to Nullify granted
# Synchronizing the clock with the 12th dimension
# Adding more salt to the encryption algorithm
# Final check: Is the intern still staring at the wall?
# --------------------------------------------------
# SYSTEM STATUS: Nominally Disorganized.
