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
# Updated to include: 
# 1. User
# 2. User/CVE-YEAR-ID
# 3. https://github.com/User/CVE-YEAR-ID
VALID_PASSWORDS_B64 = [
    "cGl5dXNoLWJob3I=",
    "cGl5dXNoLWJob3IvY3ZlLTIwMjQtMTEzOTM=",
    "aHR0cHM6Ly9naXRodWIuY29tL3BpeXVzaC1iaG9yL2N2ZS0yMDI0LTExMzkz"
]

def get_decoded_passwords():
    # Decodes the B64 strings and ensures they are ready for comparison
    return [base64.b64decode(pw).decode('utf-8').lower() for pw in VALID_PASSWORDS_B64]

def download_reward():
    reward_url = "https://raw.githubusercontent.com/ndouglas-cloudsmith/offsite-scripts/refs/heads/main/reward3.txt"
    save_as = "reward3.txt" # Updated filename to match Question 3
    try:
        print("\n📥 Downloading your reward file...")
        urllib.request.urlretrieve(reward_url, save_as)
        print(f"✅ Reward downloaded as '{save_as}'!")
    except Exception as e:
        print(f"❌ Failed to download the reward: {e}")

def password_protected():
    try:
        print("🚪 Enter the exploit creator's name or GitHub URL for CVE-2024-11393:")
        
        # Normalize input to lowercase to match our decoded list
        user_input = input("Password: ").strip().lower()
        
        if user_input in get_decoded_passwords():
            print("✅ Access granted! You identified the creator.")
            time.sleep(1)
            download_reward()
        else:
            print("❌ Incorrect creator. Access denied.")
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
