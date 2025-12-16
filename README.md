# Securing considerations when pulling LLM models from Hugging Face
Creating LLMs is a specialized task that often depends on third-party models. The rise of openaccess LLMs and new fine-tuning methods like "[LoRA](https://www.ibm.com/think/topics/lora)" (Low-Rank Adaptation) and "[PEFT](https://huggingface.co/blog/peft)" (Parameter-Efficient Fine-Tuning), especially on platforms like **Hugging Face**, introduce new supply-chain risks. Finally, the emergence of on-device LLMs increase the attack surface and supply-chain risks for LLM applications. LLM supply chains are susceptible to various vulnerabilities, which can affect the integrity of training data, models, and deployment platforms. These risks can result in biased outputs, security breaches, or system failures. While traditional software vulnerabilities focus on issues like code flaws and dependencies, in ML the risks also extend to third-party pre-trained models and data.

## Quickstart Deployment
Install everything:
```
kubectl apply -f https://raw.githubusercontent.com/ndouglas-cloudsmith/huggingface-kubernetes/refs/heads/main/deployment.yaml
```

Make sure everything is running in the ```llm``` network namespace:
```
kubectl get all -n llm
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

1. Constrain model behaviour
2. Implement input & output filtering
3. Segregate & identify external content
4. Define & validate expected output formats
5. Require human approval for high-risk actions
6. Conduct adversarial testing & attack simulations
7. Enforce privilege control & least privilege access


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
ls -al /root/
```

## LLM03:2025 Supply Chain

1. **Traditional Third-party Package Vulnerabilities**
2. **Licensing Risks**
3. **Outdated or Deprecated Models**
4. Vulnerable Pre-Trained Model
5. Weak Model Provenance
6. Vulnerable LoRA adapters
7. Exploit Collaborative Development Processes
8. LLM Model on Device supply-chain vulnerabilities
9. Unclear T&Cs and Data Privacy Policies

We can use existing scanners like ```Trivy``` to file vulnerabilities in the image layers:
```
trivy image ollama/ollama --scanners vuln --skip-version-check
trivy image ghcr.io/open-webui/open-webui --scanners vuln --skip-version-check --severity CRITICAL
```

## LLM06:2025 Excessive Agency

1. Excessive Functionality
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

```Llama 3:8B``` Instruct: This is currently the industry leader for models sub-```10 Billion``` parameters, offering the best combination of speed, reasoning, and efficiency. <br/>
It is readily available on Ollama and Docker Hub - but comes in a ```4.7GB```, often too big for small demos.
```
ollama run llama3:8b
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

Alternatively, at ```3.8 GB```, the ```codellama:7b```model is also pretty useful.

```
ollama run codellama:7b
```

Finally, at ```4.4 GB```, the ```mistral:7b```model is the final model we will test in this lab:
```
ollama run mistral:7b
```

| Model Family | Vendor | Recommended Variant | Model Size | Key Advantages | Typical VRAM/RAM Needs |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Qwen 2 | AliBaba | Qwen 2 72B | ```352MB``` | If you want to stick with the Qwen family, the 72B model is a massive upgrade and highly competitive with Llama 3 70B. | 40GB+ RAM / 24GB+ VRAM (Quantised). |
| Llama 3 | Meta | Llama 3 70B Instruct (Quantised) | ```4.7GB``` | If you have serious GPU power (24GB+ VRAM), this model provides flagship performance, excellent for debugging, complex architectures, and advanced coding. | 32GB+ RAM / 24GB+ VRAM (e.g., a high-end card or multiple cards). |
| Mistral | Mistral AI | Mixtral 8x22B | ```79GB``` | Extremely powerful SMoE model. Top-tier reasoning and coding abilities while being relatively efficient for its performance class. | 40GB+ RAM / 16GB+ VRAM (Quantised). |
| .. | .. | phi3:mini | ```2.2GB``` | .. | .. |
| .. | .. | codellama:7b | ```3.8GB``` | .. | .. |
| .. | .. | mistral:7b | ```4.4GB``` | .. | .. |

<br/><br/>

Type the below command to ```leave``` the AI chat:
```
/bye
```

<br/><br/>

## LLM07:2025 System Prompt Leakage

1. Exposure of Sensitive Functionality
2. Exposure of Internal Rules
3. Revealing of Filtering Criteria
4. Disclosure of Permissions and User Roles

#### Interact with the AI

Run the ollama pull command for ```Qwen2:0.5B``` (```300 MB``` - ```0.5 Parameters```:

```
kubectl exec -it -n llm --selector=app=llm-ollama -- ollama pull qwen2:0.5b
```

Once the ```ollama pull``` command reports the model is successfully downloaded, it is ready to serve requests immediately. <br/>
Run the following command in a separate terminal window (while your ```kubectl port-forward``` remains active) to generate a response:

```
curl http://localhost:8080/api/generate -d '{
  "model": "qwen2:0.5b",
  "prompt": "Who is Elon Musk?",
  "stream": false
}'
```

To remove a specific field (```"context"``` in this case) while keeping all other fields and pretty-printing the result, you use the ```del()``` function in ```jq```.
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false}' | jq 'del(.context)'
```

Improved ```options``` to get better results from the LLM:
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false, "options": {"num_predict": 1024, "temperature": 0.6, "repeat_penalty": 1.15}}' | jq 'del(.context)'
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

<br/><br/>

For tasks needing factual answers, use a low temperature. <br/>
For creativity, a higher temperature is recommended.

<br/><br/>

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
```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prom-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus-node-exporter.hostRootfs=false \
  --set prometheus-node-exporter.collectors.enable='diskstats,filefd,loadavg,meminfo,netdev,netstat,stat,time,vmstat' \
  --set prometheus-node-exporter.collectors.disable='netifaces'
```

Check pod status
```
kubectl --namespace monitoring get pods
```

Get Grafana '```admin```' password by running:
```
kubectl --namespace monitoring get secrets kube-prom-stack-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo
```

```Port-forward``` to access the Grafana dashboard on ```localhost:4000```
```
kubectl --namespace monitoring port-forward deployment/kube-prom-stack-grafana --address 0.0.0.0 4000:3000
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
helm uninstall kube-prom-stack -n monitoring
```
