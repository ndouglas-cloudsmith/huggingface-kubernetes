import pickle
import os
import webbrowser
import h5py # Ensure you installed this earlier!

# --- 1. CRITICAL: (os.system) ---
class CriticalMalicious:
    def __reduce__(self):
        return (os.system, ("echo 'CRITICAL'",))

# --- 2. HIGH: (webbrowser.open) ---
class HighRisk:
    def __reduce__(self):
        return (webbrowser.open, ("http://example.com",))

# Save Pickle files
with open("test_critical.pkl", "wb") as f:
    pickle.dump(CriticalMalicious(), f)

with open("test_high.pkl", "wb") as f:
    pickle.dump(HighRisk(), f)

# --- 3. MEDIUM: Keras Lambda Layer (H5 Format) ---
# ModelScan flags Lambda layers in H5 files as MEDIUM
with h5py.File("test_medium.h5", "w") as f:
    # We create a fake Keras structure that includes a 'Lambda' layer
    # Modelscan's H5LambdaDetectScan looks for the string "Lambda" in the config
    f.attrs['model_config'] = '{"class_name": "Sequential", "config": {"layers": [{"class_name": "Lambda", "config": {"function": "..."}}]}}'

print("Files created: test_critical.pkl, test_high.pkl, test_medium.h5")
