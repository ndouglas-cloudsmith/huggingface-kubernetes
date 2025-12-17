import json
import sys

# ANSI Color Codes for terminal styling
BOLD = '\033[1m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def format_stylized_output():
    try:
        # Read raw input from curl
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            return
            
        data = json.loads(raw_input)
        
        # Parse the nested string in 'response'
        # Works for any JSON structure, not just "comparison_points"
        content = json.loads(data.get('response', '{}'))
        
        # Find the list of data (it might be named differently depending on prompt)
        # This gets the first value that is a list
        items = next((v for v in content.values() if isinstance(v, list)), None)

        if not items:
            print(f"{YELLOW}⚠️  No list found in response. Raw text: {content}{RESET}")
            return

        print(f"\n{BOLD}{CYAN}🚀 ANALYSIS REPORT{RESET}")
        print(f"{CYAN}=" * 50 + f"{RESET}\n")

        for entry in items:
            # Dynamically get keys so we aren't tied to "cloudsmith" or "sysdig"
            keys = list(entry.keys())
            if not keys:
                continue
                
            # The first key is usually the "Feature" or "Subject"
            heading_key = keys[0]
            heading_val = entry.get(heading_key, "N/A")
            
            print(f"{BOLD}🔹 {heading_val.upper()}{RESET}")
            
            # Iterate through the rest of the keys as bullet points
            for key in keys[1:]:
                detail = entry.get(key, "").strip()
                if detail:
                    # Clean up the key name for display (e.g., "cloudsmith" -> "Cloudsmith")
                    display_key = key.replace("_", " ").title()
                    print(f"  {GREEN}➔ {BOLD}{display_key}:{RESET} {detail}")
            print() # Add a newline between blocks

    except Exception as e:
        print(f"{YELLOW}❌ Error parsing JSON: {e}{RESET}")

if __name__ == "__main__":
    format_stylized_output()
