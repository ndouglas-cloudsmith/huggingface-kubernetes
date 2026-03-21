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

# --- Encrypted Gateway Constants ---
# Updated to include base64 versions of:
# 1. FINAL-FLAG
# 2. "threat_id": "FINAL-FLAG"
VALID_PASSWORDS_B64 = [
    "YjQyOTFiOGItMjcxOS00Y2IyLTgwYjktN2EyMzkxOTg2MTk3",
    "InRocmVhdF9pZCI6ICJiNDI5MWI4Yi0yNzE5LTRjYjItODBiOS03YTIzOTE5ODYxOTci"
]

def get_decoded_passwords():
    # Decodes the B64 strings and ensures they are ready for comparison
    return [base64.b64decode(pw).decode('utf-8').strip() for pw in VALID_PASSWORDS_B64]

def download_reward():
    reward_url = "https://raw.githubusercontent.com/ndouglas-cloudsmith/offsite-scripts/refs/heads/main/reward4.txt"
    save_as = "reward4.txt" 
    try:
        print("\n📥 Downloading your reward file...")
        urllib.request.urlretrieve(reward_url, save_as)
        print(f"✅ Reward downloaded as '{save_as}'!")
    except Exception as e:
        print(f"❌ Failed to download the reward: {e}")

def password_protected():
    try:
        print("🛡️ Security Check: Enter the Threat ID to proceed.")
        
        # We don't use .lower() here because UUIDs/JSON keys are often case-sensitive
        user_input = input("Threat ID: ").strip()
        
        if user_input in get_decoded_passwords():
            print("✅ Access granted! Threat ID verified. You have defeated HAL 9000")
            time.sleep(1)
            download_reward()
        else:
            print("❌ Incorrect Threat ID. Access denied.")
            time.sleep(1)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Script closed by user. Goodbye!")
        sys.exit(0)

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
