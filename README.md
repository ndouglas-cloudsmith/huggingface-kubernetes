# huggingface-kubernetes
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
  name: llm-tgi-deployment
  labels:
    app: llm-tgi
spec:
  replicas: 1 # Adjust based on your load and available GPU resources
  selector:
    matchLabels:
      app: llm-tgi
  template:
    metadata:
      labels:
        app: llm-tgi
    spec:
      # Optional: Use a node selector if you need specific GPU-enabled nodes
      # nodeSelector:
      #   gpu: nvidia
      volumes:
        # Essential for TGI. TGI requires a shared memory volume for communication.
        - name: dshm
          emptyDir:
            medium: Memory
      containers:
        - name: tgi-server
          image: ghcr.io/huggingface/text-generation-inference:latest # Use a specific tag for production
          ports:
            - containerPort: 80 # TGI default port
          env:
            # --- Model Configuration ---
            - name: MODEL_ID
              value: "microsoft/phi-2" # Replace with your chosen lightweight model
            # Recommended memory size for shared memory
            - name: SHARDED
              value: "false" # Set to true for tensor parallelism (multi-GPU)
            # --- Performance/Resource Optimization ---
            # Set to a value like 'bitsandbytes' or 'gptq' if using quantization
            # - name: QUANTIZE
            #   value: "bitsandbytes" 
            
          resources:
            requests:
              memory: "16Gi" # Adjust based on model size
              cpu: "4"
              # nvidia.com/gpu: "1" # Uncomment and adjust for GPU usage
            limits:
              memory: "20Gi" # Adjust based on model size
              cpu: "8"
              # nvidia.com/gpu: "1" # Uncomment and adjust for GPU usage
          volumeMounts:
            - mountPath: /dev/shm
              name: dshm
EOF
```

## Service
We will use a ```ClusterIP``` service type in order to run ```kubectl port-forward``` as the standard and simplest way to expose internal services like your LLM to your local machine when running Kubernetes locally (on Docker Desktop, Minikube, or K3s).

```
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: llm-tgi-service
spec:
  # CHANGED: Use ClusterIP for internal-only service access
  type: ClusterIP 
  selector:
    app: llm-tgi
  ports:
    - protocol: TCP
      port: 80 # The service port
      targetPort: 80 # The container port (TGI)
EOF
```

### Establish the Port-Forward

The ```port-forward``` command will listen on a port on your local machine (like, ```8080```) and forward all traffic to the specified service and port inside the cluster (```llm-tgi-service:80```).
```
kubectl port-forward svc/llm-tgi-service 8080:80
```

- Local Port (```8080```): This is the port you will use on your machine (eg: ```http://localhost:8080```).
- Service Name (```llm-tgi-service```): The name of the Kubernetes service.
- Service Port (```80```): The port the service is configured to listen on.

### Interact with the AI

Now, you can interact with the LLM using ```http://localhost:8080``` as the base URL, just as if it were running directly on your machine.

```
export SERVICE_URL="http://localhost:8080"

curl $SERVICE_URL/v1/chat/completions \
  -X POST \
  -d '{
    "model": "tgi",
    "messages": [
      {
        "role": "user",
        "content": "Give me a one-sentence summary of the port-forward command."
      }
    ],
    "max_tokens": 50,
    "stream": false
  }' \
  -H 'Content-Type: application/json'
```

This method is ideal for local testing as it requires no cloud resources and avoids the complexity of setting up an Ingress Controller or external Load Balancer in your local environment.
