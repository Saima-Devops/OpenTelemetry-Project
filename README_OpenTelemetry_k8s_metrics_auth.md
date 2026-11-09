# Monitoring Kubernetes Application via Open Telemetry Collector
Reference Documentation: https://opentelemetry.io/docs/

# 1. Install Prometheus on Minikube Cluster

    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 
    helm repo update
Set the Prometheus entries in .env.secrets following README.md, then install Prometheus in the default namespace.

    python dev_secrets.py prometheus --namespace default


# 2. Install Grafana on Minikube cluster:    
Please refer the below page to install Prometheus on Cluster: 

    helm repo add grafana https://grafana.github.io/helm-charts
    helm install grafana grafana/grafana


# 3. Install OpenTelemetry Agent on Minikube cluster:    

    kubectl apply --namespace default -f otel_k8s_config_auth.yaml

# 4. Validate the Data(Metrics) on Grafana

Metrics Validation:
To Search all of the time series data points grouping by job  

        count({__name__=~".+"}) by (job)