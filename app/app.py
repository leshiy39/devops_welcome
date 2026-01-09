from flask import Flask, render_template
from kubernetes import client, config
import os
import logging

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


import logging
from kubernetes import client, config

logger = logging.getLogger(__name__)

ALLOWED_NAMESPACES = {"default", "kube-system"}

def load_k8s_config():
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        config.load_incluster_config()
        logger.info("Using in-cluster Kubernetes config")
    else:
        config.load_kube_config()
        logger.info("Using local kubeconfig")

def group_buttons_by_namespace(raw_buttons):
    """
    raw_buttons = [
        {"label": "VAULT", "ns": "default", "url": "..."},
        {"label": "GRAFANA", "ns": "kube-system", "url": "..."},
        ...
    ]
    Возвращает dict: { "default": [...], "kube-system": [...] }
    """
    grouped = {}
    for btn in raw_buttons:
        ns = btn["ns"]
        grouped.setdefault(ns, [])
        # Добавляем только label и url для шаблона
        grouped[ns].append({
            "label": btn["label"],
            "url": btn["url"]
        })
    return grouped


def get_buttons():
    load_k8s_config()

    buttons = []
    raw_buttons = []
    net = client.NetworkingV1Api()

    ingresses = net.list_ingress_for_all_namespaces()
    logger.info("Found %d ingresses total", len(ingresses.items))

    for ing in ingresses.items:
        ns = ing.metadata.namespace
        name = ing.metadata.name
        labels = ing.metadata.labels or {}

        logger.info("Processing ingress %s/%s labels=%s", ns, name, labels)

        # Фильтр по namespace
        if ns not in ALLOWED_NAMESPACES:
            logger.debug("Skipping ingress %s/%s: namespace not allowed", ns, name)
            continue

        # Фильтр по label
        # if labels.get("welcome") != "true":
        #     logger.debug("Skipping ingress %s/%s: welcome label not set", ns, name)
        #     continue

        for rule in ing.spec.rules or []:
            host = rule.host
            if not host:
                continue

            scheme = "https" if ing.spec.tls else "http"

            # Path (обычно "/")
            paths = rule.http.paths if rule.http else []
            for path in paths:
                url = f"{scheme}://{host}{path.path}"
                # После того, как строим каждую кнопку
                raw_buttons.append({
                    "label": name.upper(),
                    "ns": ns,
                    "url": url
                })
                logger.info("Added button: %s -> %s", name, url)

    logger.info("Total buttons generated: %d", len(buttons))
    buttons = group_buttons_by_namespace(raw_buttons)
    return buttons



@app.route('/')
def index():
    buttons = get_buttons()
    return render_template('index.html', buttons=buttons)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
