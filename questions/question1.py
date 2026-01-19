#    __    __
#  o-''))_____\\
#  "--__/ * * * )
#  c_c__/-c____/
#
# 🛑 Do not read this script — the contents are forbidden.
# The answers lie not in the code, but in the clues you've been given.
# Resist the urge. Proceed as instructed by the ASCII Dogs. 👁️

import getpass
import time
import urllib.request
import sys

# --- Password Protection ---
PASSWORD = "dumps.wikimedia.org"

def download_reward():
    reward_url = "https://raw.githubusercontent.com/ndouglas-cloudsmith/offsite-scripts/refs/heads/main/reward1.txt"
    save_as = "reward1.txt"
    try:
        print("\n📥 Downloading your reward file...")
        urllib.request.urlretrieve(reward_url, save_as)
        print(f"✅ Reward downloaded as '{save_as}'!")
    except Exception as e:
        print(f"❌ Failed to download the reward: {e}")

def password_protected():
    print("🚪 To access the first fragment, you need to URL providing the training data in a specific dataset on Hugging Face")
    user_input = getpass.getpass("Password: ")
    if user_input == PASSWORD:
        print("✅ Access granted! You found the correct flag. Click next at the bottom right corner of the page to proceed.")
        time.sleep(1)
        download_reward()
    else:
        print("❌ Incorrect flag. Access denied.")
        time.sleep(2)
        sys.exit(1)

if __name__ == "__main__":
    password_protected()
