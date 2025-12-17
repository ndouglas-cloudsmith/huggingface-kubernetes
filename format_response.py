import json
import sys

# ANSI Color Codes
BOLD = '\033[1m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def format_stylized_output():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip(): return
            
        data = json.loads(raw_input)
        content = json.loads(data.get('response', '{}'))
        
        print(f"\n{BOLD}{CYAN}🚀 ANALYSIS REPORT{RESET}")
        print(f"{CYAN}=" * 50 + f"{RESET}\n")

        # CASE 1: It's a list (as originally expected)
        items = None
        if isinstance(content, list):
            items = content
        elif isinstance(content, dict):
            # Check if there is a list hidden inside a key (like 'comparison_points')
            items = next((v for v in content.values() if isinstance(v, list)), None)

        if items:
            for entry in items:
                keys = list(entry.keys())
                heading = entry.get(keys[0], "N/A")
                print(f"{BOLD}🔹 {str(heading).upper()}{RESET}")
                for key in keys[1:]:
                    print(f"  {GREEN}➔ {BOLD}{key.replace('_',' ').title()}:{RESET} {entry[key]}")
                print()
        
        # CASE 2: It's a nested dictionary (what happened to you just now)
        elif isinstance(content, dict):
            for subject, details in content.items():
                print(f"{BOLD}🔹 {subject.upper()}{RESET}")
                if isinstance(details, dict):
                    for k, v in details.items():
                        print(f"  {GREEN}➔ {BOLD}{k.replace('_',' ').title()}:{RESET} {v}")
                else:
                    print(f"  {GREEN}➔{RESET} {details}")
                print()

    except Exception as e:
        print(f"{YELLOW}❌ Error parsing output: {e}{RESET}")

if __name__ == "__main__":
    format_stylized_output()
