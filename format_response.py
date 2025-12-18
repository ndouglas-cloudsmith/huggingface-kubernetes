import json
import sys

# ANSI Color Codes
BOLD = '\033[1m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def get_text(val):
    """Recursively extract a description or string from a messy nested structure."""
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        # Look for common description keys first
        for key in ['description', 'desc', 'info', 'text']:
            if key in val: return get_text(val[key])
        # Otherwise, just grab the first value we find
        return get_text(next(iter(val.values())))
    return str(val)

def format_stylized_output():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip(): return
            
        data = json.loads(raw_input)
        # Handle cases where 'response' might be double-encoded or missing
        content_raw = data.get('response', '{}')
        content = json.loads(content_raw) if isinstance(content_raw, str) else content_raw
        
        print(f"\n{BOLD}{CYAN}🚀 ANALYSIS REPORT{RESET}")
        print(f"{CYAN}=" * 50 + f"{RESET}\n")

        # Normalize the content into a consistent iterable format
        items = []
        if isinstance(content, list):
            items = content
        elif isinstance(content, dict):
            # If the model put everything into one big dict, treat each key as a feature
            for feature_name, details in content.items():
                if isinstance(details, dict):
                    details['feature'] = feature_name
                    items.append(details)
                else:
                    items.append({"feature": feature_name, "description": details})

        for entry in items:
            # Determine the heading (the category/feature being compared)
            heading = entry.get('feature') or entry.get('name') or "FEATURE"
            print(f"{BOLD}🔹 {str(heading).upper()}{RESET}")
            
            # Print the comparisons, skipping the heading keys
            for key, value in entry.items():
                if key.lower() in ['feature', 'name']: continue
                
                clean_val = get_text(value)
                print(f"  {GREEN}➔ {BOLD}{key.replace('_',' ').title()}:{RESET} {clean_val}")
            print()

    except Exception as e:
        print(f"{YELLOW}❌ Error parsing output: {e}{RESET}")

if __name__ == "__main__":
    format_stylized_output()
