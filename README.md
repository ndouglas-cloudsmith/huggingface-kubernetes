# Hugging Face Kubernetes
Demo of HuggingFace AI app running on Kubernetes

## LLM Deployment Template
This example uses the ```ghcr.io/huggingface/text-generation-inference``` Docker image and deploys a lightweight model like ```microsoft/phi-2``` (ensure the image and model are compatible with your environment, especially regarding GPU/CPU and memory).

You will typically use a **Deployment** to manage the LLM application and a **Service** to expose it. <br/>
This deployment pulls the TGI image and configures it to load a specific model.

```
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: ollama-startup-script
data:
  # The startup script for the Ollama server and model pull.
  startup.sh: |
    #!/bin/bash
    
    # 1. Start the Ollama server process in the background.
    /usr/bin/ollama serve &
    
    # 2. Wait for the server to initialize.
    sleep 5
    
    # 3. Pull the required model using the Ollama client utility.
    echo "Starting model pull for qwen2:0.5b..."
    /usr/bin/ollama pull qwen2:0.5b
    
    # 4. Keep the container alive by waiting for the background server process.
    wait
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-ollama-deployment
  labels:
    app: llm-ollama
spec:
  replicas: 1
  selector:
    matchLabels:
      app: llm-ollama
  template:
    metadata:
      labels:
        app: llm-ollama
    spec:
      containers:
        - name: ollama-server
          image: ollama/ollama:latest
          # Execute the mounted startup script
          command: ["/bin/bash", "/app/startup.sh"] 
          ports:
            - containerPort: 11434
          env:
            - name: OLLAMA_HOST
              value: "0.0.0.0"
          resources:
            requests:
              memory: "6Gi"
              cpu: "2"
            limits:
              memory: "8Gi"
              cpu: "4"
          volumeMounts:
            # Mount 1: The script from the ConfigMap
            - name: script-volume
              mountPath: /app
            # Mount 2: The model storage (Ollama stores models in /root/.ollama)
            - name: model-storage
              mountPath: /root/.ollama 
              
      volumes:
        # Define 1: Volume sourced from the ConfigMap
        - name: script-volume
          configMap:
            name: ollama-startup-script
            defaultMode: 0744 # Ensure the script is executable
        # Define 2: EmptyDir volume for temporary model storage
        - name: model-storage
          emptyDir: {}
EOF
```

## Service
We will use a ```ClusterIP``` service type in order to run ```kubectl port-forward``` as the standard and simplest way to expose internal services like your LLM to your local machine when running Kubernetes locally (on Docker Desktop, Minikube, or K3s).

```
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: llm-ollama-service
spec:
  type: ClusterIP 
  selector:
    app: llm-ollama # Match the new deployment label
  ports:
    - protocol: TCP
      port: 8080 # Service port (you can choose this freely)
      targetPort: 11434 # Container port (Ollama API)
EOF
```

### Establish the Port-Forward

The ```port-forward``` command will listen on a port on your local machine (like, ```8080```) and forward all traffic to the specified service and port inside the cluster (```llm-tgi-service:80```).
```
kubectl port-forward svc/llm-ollama-service 8080:8080
```

- Local Port (```8080```): This is the port you will use on your machine (eg: ```http://localhost:8080```).
- Service Name (```llm-tgi-service```): The name of the Kubernetes service.
- Service Port (```80```): The port the service is configured to listen on.

### Interact with the AI

Define the Pod Variable (if not already done):

```
export OLLAMA_POD=$(kubectl get pods --selector=app=llm-ollama -o jsonpath='{.items[0].metadata.name}')
```

Run the ollama pull command for ```Qwen2:0.5B``` (```300 MB``` - ```0.5 Parameters```:

```
kubectl exec -it $OLLAMA_POD -- ollama pull qwen2:0.5b
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

Improved ```temperature``` options to get better results from the LLM:
```
curl -s http://localhost:8080/api/generate -d '{"model": "qwen2:0.5b", "prompt": "Who is Elon Musk?", "stream": false, "options": {"num_predict": 1024, "temperature": 0.6, "repeat_penalty": 1.15}}' | jq 'del(.context)'
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
kubectl delete deployment llm-ollama-deployment
kubectl delete service llm-ollama-service
```
