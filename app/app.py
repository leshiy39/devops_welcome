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


def get_buttons():
    buttons = []

    # Загружаем kubeconfig
    try:
        config.load_incluster_config()
        logger.info("Using in-cluster Kubernetes config")
    except config.ConfigException:
        config.load_kube_config()
        logger.info("Using local kubeconfig")

    namespace = "default"
    logger.info("Listing services in namespace: %s", namespace)

    v1 = client.CoreV1Api()
    services = v1.list_namespaced_service(namespace=namespace)

    logger.info("Found %d services total", len(services.items))

    for svc in services.items:
        name = svc.metadata.name
        labels = svc.metadata.labels or {}

        logger.info("Processing service: %s labels=%s", name, labels)

        # Фильтр по label
        # if labels.get("welcome") != "true":
        #     logger.debug("Skipping service %s: welcome label not set", name)
        #     continue

        url = None
        svc_type = svc.spec.type
        logger.info("Service %s accepted (type=%s)", name, svc_type)

        if svc_type == "NodePort":
            node_port = svc.spec.ports[0].node_port
            hostname = os.environ.get("NODE_HOST", "localhost")
            url = f"http://{hostname}:{node_port}"
            logger.info("Service %s NodePort URL: %s", name, url)

        elif svc_type == "ClusterIP":
            cluster_ip = svc.spec.cluster_ip
            port = svc.spec.ports[0].port
            url = f"http://{cluster_ip}:{port}"
            logger.info("Service %s ClusterIP URL: %s", name, url)

        elif svc_type == "ExternalName":
            url = f"http://{svc.spec.external_name}"
            logger.info("Service %s ExternalName URL: %s", name, url)

        else:
            logger.warning("Service %s has unsupported type: %s", name, svc_type)

        if url:
            buttons.append({
                "url": url,
                "label": f"{svc.metadata.namespace}/{name}"
            })
        else:
            logger.warning("Service %s skipped: URL could not be constructed", name)

    logger.info("Total buttons generated: %d", len(buttons))
    return buttons


@app.route('/')
def index():
    buttons = get_buttons()
    return render_template('index.html', buttons=buttons)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
