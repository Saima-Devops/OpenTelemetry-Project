# Send Kubernetes traces to Grafana Cloud

Fill the TRACES_TEMPO entries in .env.secrets. Set TRACES_TEMPO_AUTHORIZATION to the full HTTP authorization header value and TRACES_TEMPO_ENDPOINT to the OTLP gRPC host and port.

~~~sh
kubectl apply -f otel_traces/namespace.yaml
python dev_secrets.py traces --namespace opentelemetry-demo
kubectl apply -k otel_traces
~~~
