import pickletools
import io

def scan_pickle(file_path):
    print(f"--- Auditing: {file_path} ---")
    with open(file_path, "rb") as f:
        data = f.read()
    
    # We use genops to iterate through instructions without executing
    dangerous_found = False
    for opcode, arg, pos in pickletools.genops(data):
        # GLOBAL tells pickle to import a module
        if opcode.name == "GLOBAL":
            print(f"⚠️  WARNING: Attempting to import: {arg}")
            if "system" in arg or "eval" in arg:
                print(f"🚨 DANGER: Potential Code Execution found at position {pos}!")
                dangerous_found = True
    
    if not dangerous_found:
        print("✅ No obvious RCE globals found.")

# If you still have the 'model.pkl' from the previous step, run this:
try:
    scan_pickle("model.pkl")
except FileNotFoundError:
    print("model.pkl not found. Run the first exploit script to create it!")
