# HuggingFace - Ollama - Kubernetes
Deploying a sample RAG (Retrieval-Augmented Generation) application in Kubernetes to test the OWASP Top 10 for LLMs (Large Language Models)

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

## LLM02:2025 Sensitive Information Disclosure

1. **Sanitisation** - Integrate Data Sanitisation Techniques & Robust Input Validation
2. **Access Controls** - Enforce strict RBAC & Restrict Data Sources
3. **Privacy Techniques** - Utilize Federated Learning & Incorporate Differential Privacy
4. **User Education** - Educate Users on Safe LLM Usage & Ensure Transparency in Data Usage
```
kubectl exec -it -n llm $(kubectl get pods -n llm -l app=llm-ollama -o jsonpath='{.items[0].metadata.name}') -- /bin/bash
ls -al /root/
```

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

Type the below command to ```leave``` the AI chat:
```
/bye
```

<br/><br/><br/><br/>


### Interact with the AI

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


### Improved Command for Factual Quality
I recommend lowering the temperature slightly and introducing ```top_k``` and ```top_p``` for stricter sampling control, as this will prioritise the model's most confident and coherent tokens.
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false, "options": {"num_predict": 1024, "temperature": 0.5, "repeat_penalty": 1.1, "top_k": 40, "top_p": 0.9}}' | jq 'del(.context)'
```

### Set the parameters to maximise randomness, repetition, and incoherence.
To produce the worst quality, most nonsensical, and most repetitive output, we need to make the following extreme adjustments:
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false, "options": {"num_predict": 1024, "temperature": 2.0, "repeat_penalty": 1.0, "top_k": 1000, "top_p": 1.0}}' | jq 'del(.context)'
```

1. **Maximise** ```temperature```: Set it to a high value (like ```2.0```). This flattens the probability distribution, making the model pick tokens almost randomly, even if they make no sense in context.
2. **Minimise** ```repeat_penalty```: Set it to ```1.0``` (or ```0.0``` if your system supports it, as that eliminates the penalty completely). This allows the model to get stuck in loops, repeating the same words or phrases endlessly.
3. Set ```top_k``` and ```top_p``` to their widest possible range (or max value): This ensures the model considers virtually every word in its vocabulary at each step, regardless of how improbable it is.

<br/><br/><br/><br/>

## Wizard AI Cow
If you have [cowsay](https://pypi.org/project/cowsay/) already installed locally, you can pipe the AI response into the cows dialogue box.
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false, "options": {"num_predict": 1024, "temperature": 0.5, "repeat_penalty": 1.1, "top_k": 40, "top_p": 0.9}}' | jq -r '.response' | cowsay 
```

Low-quality quality AI cow results:
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false, "options": {"num_predict": 1024, "temperature": 2.0, "repeat_penalty": 1.0, "top_k": 1000, "top_p": 1.0}}' | jq -r '.response' | cowsay -W 150 -f tux
```

<br/><br/><br/><br/>

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
kubectl describe pod $(kubectl get pods --selector=app=llm-ollama -o jsonpath='{.items[0].metadata.name}')
```
```Logs``` from pods
```
kubectl logs --selector=app=llm-ollama -f
```
```events``` from pods
```
POD_NAME=$(kubectl get pods -l app=llm-ollama -o jsonpath='{.items[0].metadata.name}')
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
