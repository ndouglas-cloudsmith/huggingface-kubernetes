import json
import sys

def convert_to_markdown():
    try:
        # Read the raw output from the curl command (via stdin)
        raw_input = sys.stdin.read()
        data = json.loads(raw_input)
        
        # Extract and parse the nested response string
        response_content = json.loads(data['response'])
        points = response_content.get('comparison_points', [])

        if not points:
            print("No comparison points found in the JSON.")
            return

        # Build the Markdown Table
        header = "| Feature | Cloudsmith | Sysdig |"
        separator = "| :--- | :--- | :--- |"
        rows = []
        
        for item in points:
            f = item.get('feature', 'N/A')
            c = item.get('cloudsmith', 'N/A')
            s = item.get('sysdig', 'N/A')
            rows.append(f"| **{f}** | {c} | {s} |")

        # Output the table
        print("\n" + header)
        print(separator)
        print("\n".join(rows))

    except Exception as e:
        print(f"Error: Could not parse JSON. Ensure the model output matches the schema. \n{e}")

if __name__ == "__main__":
    convert_to_markdown()
