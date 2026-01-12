import pickle
import os
import webbrowser

# --- 1. CRITICAL: Shell Access ---
class CriticalMalicious:
    def __reduce__(self):
        return (os.system, ("echo 'CRITICAL DETECTED'",))

# --- 2. HIGH: Network/Browser Interaction ---
class HighRisk:
    def __reduce__(self):
        return (webbrowser.open, ("http://malicious-site.com",))

# --- 3. MEDIUM: Unsafe Keras-style patterns ---
# Note: Medium is often triggered by Lambda layers in .h5 files,
# but using a non-standard global in Pickle often defaults to Medium.
class MediumRisk:
    def __reduce__(self):
        return (print, ("Potential unsafe logging",))

# Save the files
with open("test_critical.pkl", "wb") as f:
    pickle.dump(CriticalMalicious(), f)

with open("test_high.pkl", "wb") as f:
    pickle.dump(HighRisk(), f)

with open("test_medium.pkl", "wb") as f:
    pickle.dump(MediumRisk(), f)

print("Files created: test_critical.pkl, test_high.pkl, test_medium.pkl")
