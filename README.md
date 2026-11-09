# OpenTelemetry development labs

## Start the current Kubernetes demo

The upstream demo chart installs the application and its observability stack together. Use Helm and kubectl with a development cluster that meets the [upstream resource requirements](https://opentelemetry.io/docs/demo/kubernetes-deployment/).

~~~sh
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
helm upgrade --install otel-demo open-telemetry/opentelemetry-demo --version 0.42.6 --namespace otel-demo-current --create-namespace --wait --timeout 15m
kubectl --namespace otel-demo-current port-forward svc/frontend-proxy 8080:8080
~~~

Open http://localhost:8080/ for the demo or http://localhost:8080/grafana/ for dashboards. For Docker Compose, see [the pinned upstream Docker demo](README_Docker.md).

## Configure the individual labs

Copy .env.secrets.example to .env.secrets and fill only the keys for the lab you are running. Use raw, single-line values after the first equals sign. Keep the file local. Python 3.10 or newer and kubectl are needed for dev_secrets.py.

| Lab | Secret setup |
| --- | --- |
| Grafana Cloud logs | python dev_secrets.py cloud-logs --namespace default |
| Grafana Cloud metrics, logs and traces | python dev_secrets.py cloud-signals --namespace default |
| Grafana Cloud processors | python dev_secrets.py cloud-processors --namespace default |
| Standalone Kubernetes traces | python dev_secrets.py traces --namespace opentelemetry-demo |
| Authenticated Prometheus | python dev_secrets.py prometheus --namespace default |
| Historical 1.5 demo | python dev_secrets.py demo --namespace otel-demo |

Create the namespace first and use the same namespace for the secret and its workloads. The cloud profiles share the otel-cloud-dev Secret name, so use a separate namespace or replace the existing collector when switching profiles. Restart any running collector after changing credentials. Use Grafana Cloud OTLP endpoints and credentials from your own account. Update the scrape targets in the metrics values to match your cluster.

For Prometheus, install requirements.txt with python -m pip install -r requirements.txt, then run python gen_pass.py. Store the resulting hash in PROMETHEUS_PASSWORD_HASH and the same password in PROMETHEUS_PASSWORD. Helm stores the derived dev probe header in release metadata and Kubernetes stores it in the probe spec. Keep this lab on a trusted dev cluster.

## Historical examples

The checked-in 1.5 manifests and older standalone labs are reference examples. The old Compose logs stack depends on end-of-life [Promtail](https://grafana.com/docs/loki/latest/send-data/promtail/) and the 1.5 manifests include end-of-life [Jaeger v1](https://www.jaegertracing.io/download/). The old Collector examples also use removed components, including the logging exporter. Use the chart above for the maintained demo stack. For the original Kubernetes exercise, create its secrets before applying the historical manifests.

~~~sh
kubectl create namespace otel-demo
python dev_secrets.py demo --namespace otel-demo
kubectl apply --namespace otel-demo -f opentelemetry-app -f opentelemetry-collector -f jaeger -f prometheus -f grafana
~~~
