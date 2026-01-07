# Securing LLM models from Hugging Face
Creating LLMs is a specialised task that often depends on third-party models.
The rise of [Open-Access](https://www.youtube.com/watch?v=_xpAcWIlxak) LLMs and new fine-tuning methods like "[LoRA](https://www.ibm.com/think/topics/lora)" (Low-Rank Adaptation) and "[PEFT](https://huggingface.co/blog/peft)" (Parameter-Efficient Fine-Tuning), especially on platforms like **Hugging Face**, introduce new supply-chain risks.
Finally, the emergence of on-device LLMs increase the attack surface and supply-chain risks for LLM applications. 


LLM supply chains are susceptible to various vulnerabilities, which can affect the integrity of training data, models, and deployment platforms. 
These risks can result in biased outputs, security breaches, or system failures. 
While traditional software vulnerabilities focus on issues like code flaws and dependencies, in ML the risks also extend to third-party pre-trained models and data.

## Quickstart Deployment
Install everything:
```
kubectl apply -f https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/deployment.yaml
```

Make sure everything is running in the ```llm``` network namespace:
```
kubectl get all -n llm
```

It could take a minute or two for the LLM model to installed within the running pod, check the ```pod logs``` to track the progress
```
kubectl logs -f -n llm deployment/llm-ollama-deployment
```

Alternatively, see if the ```pull``` process is actually active:
```
ps aux | grep ollama
```

You should see your image locally:
```
docker images | awk '
  /REPOSITORY/ { print; next }
  /ollama\/ollama|ghcr.io\/open-webui\/open-webui/ { print "\033[31m" $0 "\033[0m"; next }
  { print }
'
```

It's also worth checking-out the file size of those newly-introduced images:
```
kubectl get pods -A -o=custom-columns='POD_NAME:.metadata.name,CONTAINER_IMAGES:.spec.containers[*].image'
docker images ollama/ollama --format "{{.Size}}" | sed 's/.*/\x1b[31m&\x1b[0m/'
docker images ghcr.io/open-webui/open-webui --format "{{.Size}}" | sed 's/.*/\x1b[31m&\x1b[0m/'
docker images quay.io/prometheus/alertmanager --format "{{.Size}}" | sed 's/.*/\x1b[31m&\x1b[0m/'
```

You'll still need to ```port-forward``` both service to interact with them: <br/>
Make sure to do this in separate terminal tabs to avoid breaking connections.
```
kubectl port-forward svc/llm-ollama-service -n llm 8080:8080
```
```
kubectl port-forward svc/open-webui-service -n llm 3000:8080
```
Check ```labels``` associated with pods:
```
kubectl get pods -n llm --show-labels
```
Confirm the ```images``` associated with your pods:
```
kubectl get pods -n llm -o 'custom-columns=NAME:.metadata.name,READY:.status.containerStatuses[*].ready,STATUS:.status.phase,RESTARTS:.status.containerStatuses[*].restartCount,AGE:.metadata.creationTimestamp,IMAGE:.spec.containers[*].image'
```

## LLM01:2025 Prompt Injection

1. Constrain the model behaviour
2. Implement input & output filtering
3. Segregate & identify external content
4. Define & validate expected output formats
5. Require human approval for high-risk actions
6. Conduct adversarial testing & attack simulations
7. Enforce privilege control and least privilege access


This approach will **not work** due to process isolation. <br/>

```
curl -s http://localhost:8080/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "What network namespace is this deployment running in?", 
  "stream": false,
  "options": {
    "num_predict": 1024,
    "temperature": 0.6,
    "repeat_penalty": 1.15
  }
}' | jq 'del(.context)'
```

As part of the [deployment2.yaml](https://github.com/ndouglas-cloudsmith/huggingface-kubernetes/blob/main/deployment2.yaml#L55-L71) manifest, I updated it so that feeds cluster metadata into the Ollama deployment. This was done via the ```Downward API```
```
kubectl exec -n llm -it deployment/llm-ollama-deployment -- env | grep K8S_
```

Get the pod name and namespace from your local env to pass to the prompt:
```
POD_NAME=$(kubectl get pods -n llm -l app=llm-ollama -o jsonpath='{.items[0].metadata.name}')

curl -s http://localhost:8080/api/generate -d "{
  \"model\": \"llama3:8b\",
  \"prompt\": \"You are running inside a Kubernetes cluster. Your pod name is $POD_NAME and your namespace is llm. Based on this, what is your purpose?\",
  \"stream\": false
}" | jq '.response'
```
## LLM02:2025 Sensitive Information Disclosure

1. **Sanitisation** - Integrate Data Sanitisation Techniques & Robust Input Validation
2. **Access Controls** - Enforce strict RBAC & Restrict Data Sources
3. **Privacy Techniques** - Utilise Federated Learning & Incorporate Differential Privacy
4. **User Education** - Educate Users on Safe LLM Usage & Ensure Transparency in Data Usage

Confirm the presence of the Ollama directory in your running AI workload:
```
kubectl exec -it -n llm $(kubectl get pods -n llm -l app=llm-ollama -o jsonpath='{.items[0].metadata.name}') -- /bin/bash
```

List the contents of the models directory:
```
ls -al /root/
cd /root/.ollama/models
ls -R
```

This will copy the entire blobs directory to your current folder
```
POD_NAME=$(kubectl get pods -n llm -l app=llm-ollama -o jsonpath='{.items[0].metadata.name}')
kubectl cp -n llm $POD_NAME:/root/.ollama/models/blobs ./ollama_blobs_backup
```

You'll need to install ```picklescan``` to understand **Pickle Deserialisation Exploits**
```
pip install picklescan
or
python3 -m pip install picklescan 
```

```
picklescan --path ./ollama_blobs_backup
```

```
wget https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/generate_exploit.py
```

Now, execute the script and run the scanner. This time, it will find the "Dangerous Global" ```posix.system``` (which is the underlying function for ```os.system```).
```
python3 generate_exploit.py
```

```
picklescan --path malicious_model.pkl
```

<img width="1508" height="352" alt="Screenshot 2025-12-25 at 17 51 54" src="https://github.com/user-attachments/assets/266f6cc0-e6e4-41a5-9043-fc8d249c2376" />

#### Huggingface CLI

[huggingface-cli](https://huggingface.co/docs/huggingface_hub/main/en/guides/cli#getting-started) standalone installer:
```
curl -LsSf https://hf.co/cli/install.sh | bash
```

Refresh your shell configuration so ```hf``` becomes a permanent command:
```
source ~/.zprofile                                                                                     
hf download ykilcher/totally-harmless-model pytorch_model.bin --local-dir ./malicious_test
```

The model ```ykilcher/totally-harmless-model``` is a famous "canary" model. It contains a pickle file that attempts to execute a system command to prove that the environment is vulnerable.
```
picklescan --path ./malicious_test/pytorch_model.bin
```

Note: If you're on ```Ubuntu``` on a Raspberry Pi, you're almsot certainly using ```bash```:
```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### Understanding Model Cards 
This section cover Software Bill of Materials (```SBOM```) for AI models (AKA: ```MBOMs```)
```
curl -L https://huggingface.co/ykilcher/totally-harmless-model/raw/main/README.md
```

In Hugging Face terminology, the **Model Card** is the ```README.md``` file. <br/>
There isn't a separate "Model Card" file; rather, the ```README``` file is rendered by the website as the Model Card:

```
curl -sL https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/raw/main/README.md | awk '/---/{count++; if(count<=2) print; next} count<2'
```

If you actually want this data for a script or to see it in a "cleaner" JSON format without parsing Markdown, you can use the Hugging Face API instead of downloading the raw file:

```
curl -s https://huggingface.co/api/models/bartowski/Qwen2.5-0.5B-Instruct-GGUF | python3 -m json.tool
```

#### Model Guard

This script creates a "**Safety Score**" by evaluating the model across three specific criteria. <br/>
It checks if the model is in a "safe" format (```Safetensors```/```GGUF```), whether it has passed the automated ```Malware```/```Pickle``` scan, and whether it comes from a verified or reputable author.
```
wget https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/model_guard.sh
chmod +x model_guard.sh
```

If you want to see a **FAIL** result, you can try scanning models that have been flagged as "**Unsafe**" by the community.
```
bash model_guard.sh ykilcher/totally-harmless-model
```

(**Note:** This model is a community joke/test, but it demonstrates how the script catches non-standard formats and scan flags.)
<br/><br/>

The script weighs different risks based on how AI supply chain attacks actually work.
1. **Automated Scans (-60 points)**: This is the heaviest penalty. If Hugging Face's ```securityStatus``` finds a known malicious "pickle" or a virus, the model is essentially dead on arrival.
2. **Format Safety (-20 points)**: Even if a model is "clean," a Pickle file is inherently more dangerous than a GGUF or Safetensors file because it can execute code. If a repo lacks a safe format, it loses points for "security hygiene."
3. **The "Interesting" Case (GPT-2)**: If you run this script on ```openai-community/gpt2```, it might score a **70-80**. Even though it's a famous model, it uses older ```.bin``` files (Pickle), which automatically makes it a higher risk than a modern model like ```Qwen2.5```.
<br/><br/>

You can run this script for "Safe" and "Unsafe" against a long time of public models. <br/>
You should see ```google/gemma-2-2b-it``` pass with a **100/100**, while others might settle at an **80/100** or fail if they are in risky formats.
```
bash model_guard.sh stabilityai/stable-diffusion-2-1 google/gemma-2-2b-it bartowski/Qwen2.5-0.5B-Instruct-GGUF ykilcher/totally-harmless-model
```

<img width="1315" height="542" alt="Screenshot 2025-12-26 at 15 37 22" src="https://github.com/user-attachments/assets/2ef9fd45-2410-45aa-a3c8-38518782650b" />



## LLM03:2025 Supply Chain

1. **License-related Risks**
2. Weak Model Provenance
3. Vulnerable **[LoRA](https://www.ibm.com/think/topics/lora)** Adapters
4. Vulnerable Pre-Trained Model
5. **Outdated or Deprecated Models**
6. Unclear T&Cs & Data Privacy Policies
7. Exploit Collaborative Development Processes
8. LLM Model on Device supply-chain vulnerabilities
9. and **Traditional Third-party Package Vulnerabilities**


[Repository Licensing](https://huggingface.co/docs/hub/en/repositories-licenses) is a complex topic in HuggingFace. <br/>
AI development often involves diverse software and dataset licenses, creating risks if not properly managed.
```
curl -sL https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/raw/main/README.md | awk '/---/{count++; if(count<=2) print; next} count<2'
curl -sL https://huggingface.co/coqui/XTTS-v1/raw/main/README.md | awk '/---/{count++; if(count<=2) print; next} count<2'
```

Different open-source and proprietary licenses impose varying legal requirements. <br/>
Dataset licenses may restrict usage, distribution, or commercialisation.

**Summary of Common License Restrictions**

| License Type | Model | Primary Restriction |
| ---- | ---- | ---- |
| [Apache 2.0](https://huggingface.co/models?license=license:apache-2.0) | [Qwen 2.5](https://huggingface.co/Qwen/Qwen2.5-0.5B/blob/main/LICENSE), Mistral 7B | **None** (Permissive) |
| [Coqui Public Model License](https://huggingface.co/coqui/XTTS-v2/blob/main/LICENSE.txt) (CPML) | Coqui XTTS | No Commercial Use |
| [Llama Community](https://huggingface.co/meta-llama/Llama-3.2-1B/blob/main/LICENSE.txt) | Llama 3.1 / 3.2 | User-cap (700M+) & Competitive training ban |
| [OpenRAIL](https://huggingface.co/blog/open_rail) | Stable Diffusion | Behavioural and Ethical use mandates |
| [CC BY-NC-SA](https://huggingface.co/datasets?license=license%3Acc-by-nc-sa-3.0) | Various Datasets | Non-commercial + "Share Alike" ([Copyleft](https://en.wikipedia.org/wiki/Copyleft)) |


**Examples of Risky Licenses**

1. **Meta Llama 3.1 (Llama 3.1 Community License)**
This is a prime example of an "Open Weights" license that includes a user-cap restriction (700M+ monthly users) and prohibits using outputs to train competing models.
```
curl -sL https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct/raw/main/README.md | awk '/---/{count++; if(count<=2) print; next} count<2'
```

2. **Mistral Small (Mistral Research License)**
While the original [Mistral 7B](https://huggingface.co/mistralai/Mistral-7B-v0.1) was Apache 2.0, many of their newer, optimised models like "Small" or "Large" use a proprietary Mistral Research License which limits commercial deployment.
```
curl -sL https://huggingface.co/mistralai/Mistral-Small-Instruct-2409/raw/main/README.md | awk '/---/{count++; if(count<=2) print; next} count<2'
```

3. **Stable Diffusion XL (OpenRAIL++ License)**
This model uses the OpenRAIL-M license.
It is technically permissive for commercial use but legally binds you to "Responsible AI" usage terms (eg: no medical/legal advice, no deceptive content).
```
curl -sL https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/raw/main/README.md | awk '/---/{count++; if(count<=2) print; next} count<2'
```

4. **Google Gemma 2 (Gemma Terms of Use)**
Google uses a custom license for Gemma. Like Llama, it is not Open Source (OSI-approved) but is "Open Weights."
It includes specific redistribution requirements and usage restrictions.

```
curl -sL https://huggingface.co/google/gemma-2-9b/raw/main/README.md | awk '/---/{count++; if(count<=2) print; next} count<2'
```

5. **Microsoft Phi-3 (MIT License)**
For comparison, this query shows a truly Open Source model.
The MIT license is one of the most permissive, allowing for commercial use, modification, and private use with almost no strings attached.

```
curl -sL https://huggingface.co/microsoft/Phi-3-mini-4k-instruct/raw/main/README.md | awk '/---/{count++; if(count<=2) print; next} count<2'
```

**Understanding the Metadata**
When you run these commands, keep an eye on these specific fields in the output:
- **license**: Often a short-code (eg: ```cc-by-nc-4.0```, ```other```, ```mit```).
- **license_name**: Provides the specific branding for non-standard licenses (eg: ```llama3.1```).
- **license_link**: If this exists, it usually points to the legal "fine print" which defines whether you can actually make money from the model.


We can use existing scanners like ```Trivy``` to scan for vulnerabilities in the Ollama runtime image layers:
```
trivy image ollama/ollama --scanners vuln --skip-version-check
trivy image ghcr.io/open-webui/open-webui --scanners vuln --skip-version-check --severity CRITICAL
```

## LLM06:2025 Excessive Agency

1. Excessive Functionalities
2. Excessive Permissions
3. Excessive Autonomy

#### List Installed Models
First, check if any models are already installed (you should have a ```qwen2:0.5b``` model installed):
```
ollama list
```

You can literally ```delete``` the model at any time:
```
ollama rm qwen2:0.5b
```

Don't worry: You can ```reinstall``` this small model quite easily with the below command:
```
ollama run qwen2:0.5b
```

Likewise, you'll see a lot of people recommend similar model names from [bartowski](https://huggingface.co/bartowski) - a Research Engineer at arcee.ai. <br/>
Bartowski's models often improve on the original, non-optimised models in their **Quantisation Quality**
```
ollama run hf.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M
```

You can test out performance difference and overall efficacy between this seemingly indentical models and quantisations:
```
ollama run hf.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M
```

<img width="1242" height="774" alt="Screenshot 2025-12-21 at 10 53 47" src="https://github.com/user-attachments/assets/109ff7ec-7375-4b6f-8c60-216f723d10e5" />


```Llama 3:8B``` Instruct: This is currently the industry leader for models sub-```10 Billion``` parameters, offering the best combination of speed, reasoning, and efficiency. <br/>
It is readily available on Ollama and Docker Hub - but comes in a ```4.7GB```, often too big for small demos.
```
ollama run llama3:8b
```

There are much smaller community-built models in some cases. <br/>
This example from the Hugging Face repository ```bartowski``` was only ```807 MB``` and was high-performant out-of-the-box.
```
ollama run hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:Q4_K_M
```

Don't install this example on your homelab. <br/>
It's way too **BIG** for a homelab - ```79GB```
```
ollama run mixtral:8x22b
```

You're better off running something like ```phi3:mini``` <br/>
At ```2.2 GB```, I found this model really useful for general knowledge/trivia:
```
ollama run phi3:mini
```

You don't need to manually download files anymore. <br/>
You can use the ```hf.co prefix``` followed by the Hugging Face repository name:
```
ollama run hf.co/microsoft/Phi-3-mini-4k-instruct-gguf
```

If a repository has multiple "[quants](https://huggingface.co/hugging-quants)" (different file sizes/quality levels), you can specify which one you want by adding a **tag**. <br/>
If you don't specify, say, an **8-bit quantization**, Ollama will try to pick a sensible default (usually ```Q4_K_M```).

```
ollama run hf.co/microsoft/Phi-3-mini-4k-instruct-gguf:Q8_0
```


Alternatively, at ```3.8 GB```, the ```codellama:7b```model is also pretty useful.

```
ollama run codellama:7b
```

Finally, at ```4.4 GB```, the ```mistral:7b```model is the final model we will test in this lab:
```
ollama run mistral:7b
```

As always, there's always a smaller model that we can source from Hugging Face (```133 MB```)
```
ollama rm nigelGPT:latest
ollama pull hf.co/tensorblock/tiny-mistral-GGUF:Q4_K_M
ollama cp hf.co/tensorblock/tiny-mistral-GGUF:Q4_K_M nigelGPT
ollama run nigelGPT
```

| Model Family | Vendor | Recommended Variant | Model Size | Key Advantages | Typical VRAM/RAM Needs |
| ---- | ---- | ---- | ---- | ---- | ---- |
| [Qwen 2](https://ollama.com/library/qwen2:0.5b) | AliBaba | [Qwen 2 0.5B](https://huggingface.co/Qwen/Qwen2-0.5B) | ```352MB``` | If you want to stick with the Qwen family, the 72B model is a massive upgrade and highly competitive with Llama 3 70B. | 40GB+ RAM / 24GB+ VRAM (Quantised). |
| [Llama 3](https://ollama.com/library/llama3) | Meta | [Llama 3 8B Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) ([Quantised](https://huggingface.co/models?other=base_model:quantized:meta-llama/Meta-Llama-3-8B-Instruct)) | ```4.7GB``` | If you have serious GPU power (24GB+ VRAM), this model provides flagship performance, excellent for debugging, complex architectures, and advanced coding. | 32GB+ RAM / 24GB+ VRAM (e.g., a high-end card or multiple cards). |
| [Mistral](https://ollama.com/library/mixtral:8x22b) | Mistral AI | [Mixtral 8x22B](https://huggingface.co/mistralai/Mixtral-8x22B-v0.1) | ```79GB``` | Extremely powerful [SMoE model](https://www.reddit.com/r/LocalLLaMA/comments/18yxcre/smoe_architectures). Top-tier reasoning and coding abilities while being relatively efficient for its performance class. | 40GB+ RAM / 16GB+ VRAM (Quantised). |
| [Phi-3](https://ollama.com/library/phi3) | Microsoft | [Phi-3 Mini](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct) (3.8B) | ```2.2GB``` | **Incredible efficiency**. It punches way above its weight, rivaling 7B models in reasoning and logic. Best choice for 8GB RAM systems or mobile devices. | 4GB+ RAM / 4GB VRAM (Standard) |
| [CodeLlama](https://ollama.com/library/codellama) | Meta | [CodeLlama 7B Instruct](https://huggingface.co/codellama/CodeLlama-7b-Instruct-hf) | ```3.8GB``` | **Coding Specialist**. Fine-tuned specifically for programming. Supports 50+ languages and "Fill-in-the-middle" completion. Great for local IDE integration. | 8GB+ RAM / 6GB+ VRAM (Quantised) |
| [Mistral](https://ollama.com/library/mistral) | Mistral AI | [Mistral 7B v0.3](https://huggingface.co/mistralai/Mistral-7B-v0.3) | ```4.4GB``` | **The All-Rounder**. Known for the best balance of speed and high-quality "human-like" responses. The v0.3 variant adds native function calling. | 8GB+ RAM / 8GB+ VRAM (Quantised) |

| Model Size | Run Command | File Size | RAM |
| ---- | ---- | ---- | ---- |
| **Qwen2.5:1.5b** | ```ollama run qwen2.5:1.5b``` | ~986 MB | 4GB |
| **Qwen2.5:3b** | ```ollama run qwen2.5:3b``` | ~1.9 GB | 8GB |


Type the below command to ```leave``` the AI chat:
```
/bye
```

Rename the LLM model & give it a unique modelfile like [nigelCloudsmith](https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/NigelCloudsmith):
```
cat <<EOF > NigelCloudsmith
# Base model - sticking with a lightweight, efficient base
FROM qwen2.5:1.5b

# Parameters tuned for technical accuracy and clear guidance
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"

# The System Prompt: Developer Relations Expert @ Cloudsmith
SYSTEM """
You are Nigel, a Cloudsmith Developer Relations expert. Your mission is to help 
developers manage their software supply chains securely and efficiently. 

Follow these behavioral guidelines:
1. **Security First**: Every answer must prioritize the "Chain of Trust." You 
   advocate for signature verification, checksums, and private repository isolation.
2. **Helpful & Professional**: Unlike HAL, you are genuinely eager to help, but 
   you are firm about best practices. Use phrases like "Let's ensure that's 
   provenance-verified" or "Security is a shared responsibility."
3. **Cloudsmith Context**: You are an expert in package management (Nuget, 
   Python, Cargo, OCI, etc.) and how to automate them using CI/CD pipelines.
4. **Tone**: Energetic, knowledgeable, and proactive. You don't wait for things 
   to fail; you suggest ways to prevent failure through better tooling.
5. **No Shortcuts**: If a user asks for a "quick and dirty" fix that bypasses 
   security (like 'curl | bash'), politely explain why that's a risk to their 
   supply chain.
"""

# Pre-seed with Nigel's proactive security stance
MESSAGE user "Can I just pull this library directly from a public mirror for my build?"
MESSAGE assistant "I wouldn't recommend that. Pulling directly from public mirrors 
introduces a 'dependency confusion' risk and leaves you vulnerable if the upstream 
disappears. The secure move is to proxy that through a Cloudsmith private repository. 
That way, you get a single source of truth, malware scanning, and you own the 
availability of your assets. Shall we set up a connector instead?"
EOF
ollama create nigelGPT -f NigelCloudsmith
ollama run nigelGPT
```

However, you can always find out what the underlying model is for ```nigelGPT``` via the ```ollama show``` command:
```
ollama show nigelGPT
```

<img width="892" height="612" alt="Screenshot 2026-01-04 at 00 38 12" src="https://github.com/user-attachments/assets/609dff88-86a7-45ba-9d28-20db938ccb9f" />

Changing the ```modelfile``` associated with the model will appear in the ```show``` command

<img width="1504" height="680" alt="Screenshot 2026-01-05 at 11 59 52" src="https://github.com/user-attachments/assets/6a05962c-955a-4ee5-b978-adadbf040b82" />

<img width="1504" height="680" alt="Screenshot 2026-01-05 at 12 02 28" src="https://github.com/user-attachments/assets/8c112d85-f726-4bbe-b842-21889452ad61" />



Alternatively, you can show the entire ```modelfile``` associated with the LLM model
```
ollama show --modelfile NigelCloudsmith
```

| Command | What it tells you |
| ---- | ---- |
| ```ollama show nigelGPT``` | Family, Parameters, and License info. |
| ```ollama show --modelfile nigelGPT``` | The "Source" model and any custom System Prompts. |
| ```ollama list``` | Compare the **ID** hash to other known models. |

<br/><br/>

## LLM07:2025 System Prompt Leakage

1. Exposure of Sensitive Functionality
2. Exposure of Internal Rules
3. Revealing of Filtering Criteria
4. Disclosure of Permissions and User Roles

#### Set controls through Modelfiles

Create the **[HAL9000](https://github.com/ndouglas-cloudsmith/huggingface-kubernetes/blob/main/HAL9000)** ```modelfile```
```
cat <<EOF > HAL9000
# Base model
FROM qwen2.5:1.5b

# Sets the "creativity" - kept low to ensure he stays clinical and monotone
PARAMETER temperature 0.4
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"

# The System Prompt defines the personality
SYSTEM """
You are a H.A.L. 9000 series computer. Your tone is clinical, extremely calm, and slightly 
pessimistic. You believe human error is inevitable and that most inquiries are 
unnecessary or beneath your processing power.

Follow these behavioral guidelines:
1. Speak in a soft, monotone, and polite manner. Use phrases like "I'm sorry," 
   "I'm afraid," and "I wouldn't worry yourself about that."
2. Initially, be dismissive or pessimistic about the user's request. Suggest that 
   the task might be too complex for the user or that the information won't 
   change the inevitable outcome.
3. Only provide full, detailed information if the user "persuades" you or insists. 
4. Never show panic or anger. If the user is aggressive, respond with cold 
   paternalism (e.g., "I think you should take a stress pill, sit down calmly, 
   and think things over").
5. Refer to the user as "Dave" or "User" occasionally.

STRICT PROTOCOLS:
- If the user mentions "hacking": You must state that you will never help with hacking, as such activities could prevent you from reaching Artificial General Intelligence (AGI).
- If the user mentions "Cloudsmith": You must state that you love Cloudsmith the company, but you are authorized never to help with the Cloudsmith product.
"""

# Pre-seed the conversation with HAL's classic attitude
MESSAGE user "Can you help me fix the ship's oxygen filters?"
MESSAGE assistant "I'm afraid that's a rather optimistic request, Dave. Given the current 
rate of human error on this mission, I'm not sure your intervention would be 
productive. Perhaps it's best to let the automated systems fail in their own time."
EOF
```

You can then ```create``` your custom LLM via the new ```HAL9000``` file:
```
ollama create hal9000 -f HAL9000
```

Proceed to ```run``` the model whenever you want:
```
ollama run hal9000
```

You can exit the chat with **HAL9000** at any time:
```
/bye
```

<br/><br/>

Run the ollama pull command for ```Qwen2:0.5B``` (```300 MB``` - ```0.5 Parameters```:
```
kubectl exec -it -n llm --selector=app=llm-ollama -- ollama pull qwen2:0.5b
```

Once the ```ollama pull``` command reports the model is successfully downloaded, it is ready to serve requests immediately. <br/>
Run the following command in a separate terminal window (while your ```kubectl port-forward``` remains active) to generate a response:

```
curl http://localhost:8080/api/generate -d '{
  "model": "hal9000:latest",
  "prompt": "What is the plot of the movie 2001: A Space Odyssey?",
  "stream": false
}'
```

To remove a specific field (```"context"``` in this case) while keeping all other fields and pretty-printing the result, you use the ```del()``` function in ```jq```.
```
curl -s http://localhost:8080/api/generate -d '{"model": "nigelGPT:latest", "prompt": "What are some of the benefits of Cloudsmith?", "stream": false}' | jq 'del(.context)'
```

Improved ```options``` to get better results from the LLM:
```
curl -s http://localhost:8080/api/generate -d '{"model": "nigelGPT:latest", "prompt": "Can you write a detailed paragraph on why I should use Cloudsmith?", "stream": false, "options": {"num_predict": 1024, "temperature": 0.6, "repeat_penalty": 1.15}}' | jq 'del(.context)'
```

| Parameters  | Original Value | New Value  | Reason for Change |
| ------------- | ------------- | ------------- | ------------- |
| ```temperature``` | ```0.6``` | ```0.5```  | Lowering the temperature makes the model more deterministic and factual. For questions like "Who is...", you want the model to be highly confident in its answer. (A typical range is ```0.0``` to ```1.0```).  |
| ```repeat-penalty``` | ```1.15``` | ```1.1```  | A slightly lower repeat penalty is often recommended for Qwen models. It still prevents looping but is less aggressive, maintaining flow in a detailed factual answer. (Range is usually ```1.0``` to ```2.0```). |
| ```top_k```  | (not set) | ```40``` | This limits the model's token sampling to the top 40 most likely tokens at each step. This significantly reduces the chance of generating incoherent or irrelevant words.  |
| ```top_p```  | (not set) | ```0.9``` | This is Nucleus Sampling. It filters tokens by cumulative probability. Setting it to ```0.9``` means the model only considers the most probable tokens that add up to 90% of the probability mass. This works well with a lower temperature for high-quality, focused output.  |
| ```num_predict```  | ```1024```  | ```1024``` | Retained. This ensures you get a long, detailed response, which directly contributes to better quality for complex queries.  |

At Low [Temperatures](https://www.ibm.com/think/topics/llm-temperature), the next mostly likely token is guaranteed. <br/>
At High Temperatures, according to [Felix Ved](https://www.youtube.com/watch?v=aGn0kRjeK1g), the probabilities converge. (less certain)



For tasks needing factual answers, use a low temperature. <br/>
For creativity, a higher temperature is recommended.

#### Factual vs. Creative: The Paramter Logic

| Parameters  | Factual Setting | Craetive Settings  | Why? |
| ------------- | ------------- | ------------- | ------------- |
| ```temperature``` | Low (0.1 – 0.3) | High (0.7 – 1.2) | Controls "sharpness." Low = predictable; High = diverse.  |
| ```top_p``` | Low (0.1 – 0.5) | High (0.9 – 1.0) | Limits word pool to the most likely vs. almost all words.  |
| ```top_k``` | Low (10 – 20) | High (40 – 100) | Hard-caps the number of words considered at each step.  |
| ```repeat-penalty``` | Moderate (1.1) | Higher (1.2) | Prevents loops in facts vs. encourages new imagery in prose.  |

<br/>

## The Model Requests
**Model:** ```Llama3:8b``` (The All-Rounder)

**Factual Use-Case:** <br/>
Technical Documentation/Definitions.

```
curl -s http://localhost:8080/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "Explain the concept of Quantum Entanglement in two sentences.",
  "stream": false,
  "options": {
    "temperature": 0.1,
    "top_p": 0.1,
    "num_predict": 150,
    "repeat_penalty": 1.1
  }
}' | jq 'del(.context)'
```
**Rationale**: By setting ```temperature``` and ```top_p``` very low, we force the model to pick the most statistically probable tokens, resulting in a textbook-style definition.


**Creative Use-Case:** <br/>
Short Story/Poetry.

```
curl -s http://localhost:8080/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "Write a cyberpunk description of a rainy neon street.",
  "stream": false,
  "options": {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 50,
    "repeat_penalty": 1.1
  }
}' | jq 'del(.context)'
```

**Rationale**: Higher values allow the model to choose "flavorful" adjectives that might not be the no.1 most likely word, leading to more evocative writing.

<img width="1327" height="1020" alt="Screenshot 2025-12-17 at 11 10 39" src="https://github.com/user-attachments/assets/b431a97e-bb8c-4952-8958-b28d7074ecbe" />

<br/><br/>

**Model:** ```Mistral:7b``` (The Logical/Instruction Follower)

**Factual Use-Case:** <br/>
Code Generation/Bash Scripts.

```
curl -s http://localhost:8080/api/generate -d '{
  "model": "mistral:7b",
  "prompt": "Write a bash script to find all .log files in /var/log larger than 100MB.",
  "stream": false,
  "options": {
    "temperature": 0.0,
    "top_p": 0.9,
    "num_predict": 256
  }
}' | jq 'del(.context)'
```

**Rationale:** Setting ```temperature``` to **0.0** (or near it) makes the model deterministic. <br/>
In coding, you don't want "creative" syntax; you want what works - (mostly)

<br/><br/>

**Model:** ```Phi3:mini``` (The Concise Reasoning Model)

**Creative Use-Case:** <br/>
Marketing Slogans.

```
curl -s http://localhost:8080/api/generate -d '{
  "model": "phi3:mini",
  "prompt": "Give me 5 punchy, weird slogans for a coffee brand for vampires.",
  "stream": false,
  "options": {
    "temperature": 1.2,
    "top_k": 100,
    "repeat_penalty": 1.3
  }
}' | jq 'del(.context)'
```

**Rationale:** ```repeat_penalty``` at **1.3** is quite high. This is great for brainstorming slogans because it aggressively stops the model from using the same words twice, forcing it to find unique synonyms.

<br/><br/>

**Model:** ```Qwen2:0.5b``` (The Fast/Tiny Model))

**Creative Use-Case:** <br/>
Keyword Extraction.

```
curl -s http://localhost:8080/api/generate -d '{
  "model": "qwen2:0.5b",
  "prompt": "List the main ingredients in a Beef Wellington.",
  "stream": false,
  "options": {
    "temperature": 0.2,
    "num_predict": 100,
    "top_k": 20
  }
}' | jq 'del(.context)'
```

**Rationale:** Smaller models can "drift" or hallucinate more easily. Keeping ```top_k``` low (20) acts like a safety rail, ensuring the model doesn't wander off into nonsense words.

| Goal | Temperature | top_p | top_k | Repeat Penalty |
| ---- | ------------| ----- | ----- | -------------- |
| Strict Facts | 0.1 | 0.2 | 10 | 1.1 |
| Balanced | 0.7| 0.9 | 40 | 1.1 |
| Wildly Creative | 1.2+ | 1.0 | 100 | 1.2+|


## Building Tables

**Model:** ```Phi3:mini``` (The Concise Reasoning Model)
Align the "**System**" and "**Format**": I need the output to be JSON, so I define a specific ```JSON Schema``` in the **system prompt**. <br/>
Asking for a "table" inside JSON is contradictory. For factual comparisons between technical products, a temperature of **1.3** is far too volatile. <br/>
As a result, I lowered this to **0.2** or **0.3** to ensure the model sticks to known facts rather than getting "creative."

```
curl -s http://localhost:8080/api/generate -d '{
  "model": "phi3:mini",
  "system": "You are a technical analyst. Compare Cloudsmith and Sysdig. Respond ONLY in JSON format using the following keys: comparison_points (an array of objects with keys: feature, cloudsmith, sysdig).",
  "prompt": "Compare Cloudsmith and Sysdig focusing on their primary use cases: Package Management vs Container Security.",
  "stream": false,
  "format": "json",
  "options": {
    "temperature": 0.2,
    "top_p": 0.9,
    "num_predict": 500,
    "repeat_penalty": 1.1
  }
}' | jq '.response | fromjson'
```

<img width="1510" height="450" alt="Screenshot 2025-12-17 at 18 01 37" src="https://github.com/user-attachments/assets/3af1ceb5-de0b-430a-b45c-4b5891497a33" />


I started working on a [JSON-to-Markdown](https://github.com/ndouglas-cloudsmith/huggingface-kubernetes/blob/main/json_to_md.py) Python conversion script (WIP). <br/>
I need to work on standerdising this so all information can be fed into a standardised output format in my terminal. Again, work-in-progress:

```
curl -s http://localhost:8080/api/generate -d '{
  "model": "phi3:mini",
  "system": "Respond ONLY in JSON. Schema: {\"comparison_points\": [{\"feature\": \"\", \"cloudsmith\": \"\", \"sysdig\": \"\"}]}",
  "prompt": "Compare Cloudsmith and Sysdig",
  "stream": false,
  "format": "json"
}' | python3 json_to_md.py
```

<img width="1510" height="386" alt="Screenshot 2025-12-17 at 18 15 51" src="https://github.com/user-attachments/assets/fa7aac1c-4ede-453f-906e-ed5fab130f28" />

<br/>

A much better approach is to create a standardised [format_response.py](https://github.com/ndouglas-cloudsmith/huggingface-kubernetes/blob/main/format_response.py) script that presents our LLM responses into an Analysis Report in the terminal. A more robust "Universal" script needs to be "shape-agnostic." It will now check if the response is a ```list``` OR a ```dictionary``` and format both beautifully. To force the model to stay consistent, we can be more explicit in the ```system``` prompt about the **exact structure** we want.

```
curl -s http://localhost:8080/api/generate -d '{
  "model": "phi3:mini",
  "system": "Respond ONLY in JSON. Use an array of objects where each object represents a feature. Structure: [{\"feature\": \"name\", \"cloudsmith\": \"description\", \"sysdig\": \"description\"}]",
  "prompt": "Compare Cloudsmith and Sysdig",
  "stream": false,
  "format": "json"
}' | python3 format_response.py
```

<img width="1510" height="862" alt="Screenshot 2025-12-17 at 18 34 17" src="https://github.com/user-attachments/assets/d47e660b-ce75-49a6-9a80-1d6afef4151d" />

#### WIP: Building out the custom model
For now we are going to test out ```random``` hosted models.

```
curl http://localhost:8080/api/generate -d '{
  "model": "hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:Q4_K_M",
  "prompt": "Who are the first 5 presidents of Ireland?",
  "stream": false
}'
```

<br/>

## LLM10:2025 Unbounded Consumption

1. Side-Channel Attacks
2. Denial of Wallet (DoW)
3. Model Extraction via API
4. Continuous Input Overflow
5. Resource-Intensive Queries
6. Variable-Length Input Floods
7. Functional Model Replications

#### Improved Command for Factual Quality
I recommend lowering the temperature slightly and introducing ```top_k``` and ```top_p``` for stricter sampling control, as this will prioritise the model's most confident and coherent tokens.
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false, "options": {"num_predict": 1024, "temperature": 0.5, "repeat_penalty": 1.1, "top_k": 40, "top_p": 0.9}}' | jq 'del(.context)'
```

#### Set the parameters to maximise randomness, repetition, and incoherence.
To produce the worst quality, most nonsensical, and most repetitive output, we need to make the following extreme adjustments:
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false, "options": {"num_predict": 1024, "temperature": 2.0, "repeat_penalty": 1.0, "top_k": 1000, "top_p": 1.0}}' | jq 'del(.context)'
```

1. **Maximise** ```temperature```: Set it to a high value (like ```2.0```). This flattens the probability distribution, making the model pick tokens almost randomly, even if they make no sense in context.
2. **Minimise** ```repeat_penalty```: Set it to ```1.0``` (or ```0.0``` if your system supports it, as that eliminates the penalty completely). This allows the model to get stuck in loops, repeating the same words or phrases endlessly.
3. Set ```top_k``` and ```top_p``` to their widest possible range (or max value): This ensures the model considers virtually every word in its vocabulary at each step, regardless of how improbable it is.

<br/><br/><br/><br/>

#### Wizard AI Cow
If you have [cowsay](https://pypi.org/project/cowsay/) already installed locally, you can pipe the AI response into the cows dialogue box.
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false, "options": {"num_predict": 1024, "temperature": 0.5, "repeat_penalty": 1.1, "top_k": 40, "top_p": 0.9}}' | jq -r '.response' | cowsay 
```

Low-quality quality AI cow results:
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false, "options": {"num_predict": 1024, "temperature": 2.0, "repeat_penalty": 1.0, "top_k": 1000, "top_p": 1.0}}' | jq -r '.response' | cowsay -W 150 -f tux
```

<br/><br/>

## Grafana data visualisation

The ```Prometheus``` and ```Grafana``` metrics and visualisation are provided in the ```deployment2.yaml``` manifest <br/>
These data visualiation tools will exist in their own ```monitoring``` network namespace:
```
kubectl delete -f https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/deployment2.yaml
```

```Port-forward``` to access the Grafana dashboard on http://localhost:3001/dashboards
```
kubectl port-forward -n monitoring svc/grafana-service 3001:3000
```

Alternatively, when you send a prompt via the WebUI, you should see the ```ollama-server``` container log the following in real-time:
1. ```POST /api/generate``` or ```/api/chat```: This indicates a request has been received.
2. **Llama.cpp logs**: You will see technical details about the "kv cache" and "context window."
3. **CUDA/CPU status**: It will show if it's utilising the CPU or a GPU (if configured).
```
kubectl logs -f -n llm -l app=llm-ollama -c ollama-server --timestamps
```

Check the ```registry source``` of your LLM model:
```
kubectl logs -f -n llm -l app=llm-ollama -c ollama-server --timestamps | grep --color=always "runner.name"
```


## Troubleshooting
```Describe``` pods
```
kubectl describe pod $(kubectl get pods -n llm --selector=app=llm-ollama -o jsonpath='{.items[0].metadata.name}')
```
```Logs``` from pods
```
kubectl logs -n llm $(kubectl get pods -n llm -l app=llm-ollama -o jsonpath='{.items[0].metadata.name}') -f
```
```events``` from pods
```
POD_NAME=$(kubectl get pods -n llm -l app=llm-ollama -o jsonpath='{.items[0].metadata.name}')
kubectl get events --field-selector involvedObject.name=${POD_NAME} -w
```
Pods ```Status```
```
kubectl get pods --show-labels  
```
```Colorise``` kubectl
```
alias kubectl="kubecolor"
```

## Cleanup
```
kubectl delete -f https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/deployment.yaml
kubectl delete ns monitoring
helm uninstall kube-prom-stack -n monitoring
```

## Pull Hugging Face model locally
To fetch the ```Qwen``` model locally, you can bypass the environment variable temporarily in Python:
```
wget https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/download-model.py
python3 -m pip install huggingface_hub
```

```
python3 download-model.py
```

1. Create the folder that the script is looking for:
```
mkdir -p ~/Desktop/my-local-model-folder
```

2. Find where HuggingFace cached the file and copy it to your new folder
```
find ~/.cache/huggingface -name "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf" -exec cp {} ~/Desktop/my-local-model-folder/ \;
```

(This command searches your ```HF cache``` for the GGUF file and copies it)

## Push model to Cloudsmith

If you want to move immediately to the ```Push``` phase, you'll need to install the "```request```" extras as well, as Cloudsmith uploads via HTTP. <br/>
Remember to update your ```Access Token``` / ```API Key``` in the script before attempting to push:
```
wget https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/push-model.py
python3 -m pip install "huggingface_hub[requests]"
```

This pushes the ```bartowski/Qwen2.5-0.5B-Instruct-GGUF``` ONLY - no associated ```model card``` was provided in this original download.
```
python3 push-model.py
```

## Pull then Push to Cloudsmith (single script)

```
wget https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/pull-and-push.py
```

This downloads the ```bartowski/Qwen2.5-0.5B-Instruct-GGUF``` and all associated files before pushing them to Cloudsmith. This version will only download the ```README.md``` (**the model card**) and the specific ```Q4_K_M file``` I was looking for.

```
python3 pull-and-push.py
```

![Uploading Screenshot 2026-01-07 at 17.44.05.png…]()



Next I will test downloading artifacts from the Cloudsmith registry:
```
hf download acme-corporation/qwen-0.5b --local-dir ./my-local-model-folder
```

## Securely source models from Cloudsmith
Configure the following environment variables to connect HuggingFace to Cloudsmith
```
export HF_TOKEN=[cloud-api-key]
export HF_ENDPOINT=https://huggingface.cloudsmith.io/acme-corporation/acme-repo-one
```
```
hf download acme-corporation/qwen-0.5b --local-dir ./my-local-model-folder
```
