import argparse
import base64
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parent
CLOUD_PROFILES = {
    "cloud-logs": "otel_k8s_logs_values.yaml",
    "cloud-signals": "otel_k8s_metrics_logs_traces_values.yaml",
    "cloud-processors": "otel_k8s_metrics_processors.yaml",
}


def load_env(path):
    values = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or key in values:
            raise ValueError("Invalid or duplicate entry in the secrets file.")
        values[key] = value
    return values


def require(values, keys):
    missing = [key for key in keys if not values.get(key)]
    if missing:
        raise ValueError("Set these entries in .env.secrets: " + ", ".join(missing))
    return {key: values[key] for key in keys}


def collector_env(values, config):
    text = (ROOT / config).read_text(encoding="utf-8")
    keys = sorted(set(re.findall(r"\$\{env:([A-Z][A-Z0-9_]*)\}", text)))
    return require(values, keys)


def apply_secret(namespace, name, data):
    manifest = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": name, "namespace": namespace},
        "type": "Opaque",
        "data": {key: base64.b64encode(value.encode()).decode("ascii") for key, value in data.items()},
    }
    subprocess.run(
        ["kubectl", "apply", "--server-side", "--field-manager=otel-dev-secrets", "-f", "-"],
        input=json.dumps(manifest), text=True, check=True,
    )


def install_prometheus(namespace, values):
    required = require(values, ["PROMETHEUS_USERNAME", "PROMETHEUS_PASSWORD", "PROMETHEUS_PASSWORD_HASH"])
    username = required["PROMETHEUS_USERNAME"]
    password = required["PROMETHEUS_PASSWORD"]
    password_hash = required["PROMETHEUS_PASSWORD_HASH"]
    if ":" in username or not re.fullmatch(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}", password_hash):
        raise ValueError("Use a username without a colon and a bcrypt hash from gen_pass.py.")
    auth = "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    apply_secret(namespace, "prometheus-dev", {
        "PROMETHEUS_AUTHORIZATION": auth,
        "web.yml": json.dumps({"basic_auth_users": {username: password_hash}}),
    })
    overlay = {"server": {"probeHeaders": [{"name": "Authorization", "value": auth}]}}
    subprocess.run(
        ["helm", "upgrade", "--install", "my-prometheus", "prometheus-community/prometheus",
         "--version", "29.33.0", "--namespace", namespace, "-f", str(ROOT / "prom_auth.yaml"), "-f", "-"],
        input=json.dumps(overlay), text=True, check=True,
    )


def main():
    parser = argparse.ArgumentParser(description="Provision local OpenTelemetry demo credentials.")
    parser.add_argument("profile", choices=["demo", "traces", "prometheus", *CLOUD_PROFILES])
    parser.add_argument("--namespace", required=True)
    args = parser.parse_args()
    try:
        values = load_env(ROOT / ".env.secrets")
        if args.profile == "demo":
            grafana = require(values, ["GRAFANA_ADMIN_USER", "GRAFANA_ADMIN_PASSWORD"])
            database = require(values, ["POSTGRES_USER", "POSTGRES_PASSWORD", "DATABASE_URL"])
            apply_secret(args.namespace, "opentelemetry-demo-grafana", {
                "admin-user": grafana["GRAFANA_ADMIN_USER"],
                "admin-password": grafana["GRAFANA_ADMIN_PASSWORD"],
                "ldap-toml": "",
            })
            apply_secret(args.namespace, "demo-db-dev", database)
        elif args.profile == "traces":
            data = collector_env(values, "otel_traces/data/otel-collector-config.yaml")
            apply_secret(args.namespace, "otel-traces-dev", data)
        elif args.profile == "prometheus":
            install_prometheus(args.namespace, values)
        else:
            data = collector_env(values, CLOUD_PROFILES[args.profile])
            apply_secret(args.namespace, "otel-cloud-dev", data)
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
