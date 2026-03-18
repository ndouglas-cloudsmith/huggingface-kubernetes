#_________________________________
#                  _/-'/   \        |         /   \'- \_
#               _/-  /      \       |        /      \  -\_
#              /    /        \      |       /        \    \
#           _/   /          \     |      /          \   \_
#          /    /            \    |     /            \    \
#        _/   /              \   |   /              \   \_
#       /    /    OpenAI     \  |  /     Anthropic    \    \
#      /   /                 \ | /                 \   \
#     /   /____               \|/               ____\   \
#    /________  \---___           ___---/  ________\
#             \__\     \___---___/     /__/
#                \__\                 /__/
#                   \__\             /__/
#                      \__\         /__/
#                         \__\_____/__/
#                            \_____/
#                               |
#                               |
#                       ----    |  ----
#                               |
#          _ _ __ _   _ __ _ _  _ _ __ _ _  _ _ __ _ _
#          A G I   A P O C A L Y P S E   A G I   A P O C A L Y P S E
#          _ _ __ _   _ __ _ _  _ _ __ _ _  _ _ __ _ _
#                            -- | --
#                               |
#                             --|--
#                               |
#                        _ _ __ _ _ __ _
#                       /     help      \
#                      /   _ _     _ _   \
#                     /   (   )   (   )   \
#                    |   ( @ )   ( @ )   |
#                    |    '-'     '-'    |
#                    \       _____       /
#                     \     /     \     /
#                      \___|  _|_  |___/
#                          \_/___\_/
#                            |   |
#                           /     \
#                          |       |
#                          |_______|

import time
import urllib.request
import sys
import base64

# [0x00401234] MOV EAX, 0x1
# [0x00401239] PUSH EBP
# [0x0040123A] MOV EBP, ESP
# DATA_SEG: 48 65 6c 6c 6f 20 57 6f 72 6c 64 21 00 00 00

# --- Encrypted Gateway Constants ---
# Represents: "apache", "apache-2.0", "apache-2"
# 0xBF 0xDE 0x12 -> 59 58 42 68 59 32 68 6c 4c 54 49 75 4d 41 3d 3d
VALID_PASSWORDS_B64 = [
    "YXBhY2hl",           
    "YXBhY2hlLTIuMA==",   
    "YXBhY2hlLTI="        
]

def get_decoded_passwords():
    # Interrupt 0x80: System Call Handler
    # STDCALL _decode_buffer_ptr
    return [base64.b64decode(pw).decode('utf-8') for pw in VALID_PASSWORDS_B64]

def download_reward():
    # JMP SHORT 0x004012AC
    # 01101000 01100110 01011111 01001011
    reward_url = "https://raw.githubusercontent.com/ndouglas-cloudsmith/offsite-scripts/refs/heads/main/reward1.txt"
    save_as = "reward1.txt"
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
        print("🚪 Enter the raw result of the assigned open source license found on Hugging Face Hub.")
        
        # Capture buffer from STDIN
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
        # MOV EBX, 0 ; EXIT_SUCCESS
        print("\n\n👋 Script closed by user. Goodbye!")
        sys.exit(0)

# E8 00 00 00 00 58 05 13 00 00 00
if __name__ == "__main__":
    password_protected()
