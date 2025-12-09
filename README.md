# Hugging Face Kubernetes
Demo of HuggingFace AI app running on Kubernetes

## LLM Deployment Template
This example uses the ```ghcr.io/huggingface/text-generation-inference``` Docker image and deploys a lightweight model like ```microsoft/phi-2``` (ensure the image and model are compatible with your environment, especially regarding GPU/CPU and memory).

You will typically use a **Deployment** to manage the LLM application and a **Service** to expose it. <br/>
This deployment pulls the TGI image and configures it to load a specific model.

```
cat <<EOF | kubectl apply -f -
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
          image: ollama/ollama:latest # ARM64 compatible image
          ports:
            - containerPort: 11434 # Ollama default API port
          env:
            # Set memory request higher if using a larger model like llama3:8b
            # Ollama downloads models to /root/.ollama, consider using a persistent volume
            - name: OLLAMA_HOST
              value: "0.0.0.0"
              
          resources:
            requests:
              # MINIMAL RESOURCE REQUESTS (Aiming for < 8Gi total)
              memory: "6Gi" 
              cpu: "2"
            limits:
              memory: "8Gi" 
              cpu: "4" 
          # The Ollama entrypoint will start the server. 
          # The first API call will trigger the model download.
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
  "prompt": "Write a short, three-word poem on why Cloudsmith is the coolest company.",
  "stream": false
}'
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


## Cleanup
```
kubectl delete deployment llm-tgi-deployment
kubectl delete service llm-tgi-service
```
