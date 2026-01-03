from flask import Flask, render_template
from kubernetes import client, config
import os

app = Flask(__name__)

def get_buttons():
    buttons = []
    try:
        # Внутри кластера
        config.load_incluster_config()
    except:
        # Локально для разработки
        config.load_kube_config()

    v1 = client.CoreV1Api()
    services = v1.list_service_for_all_namespaces()
    for svc in services.items:
        labels = svc.metadata.labels or {}
        # Фильтруем по label welcome=true
        if labels.get('welcome', 'false') != 'true':
            continue

        url = None
        # Если есть NodePort, используем его
        if svc.spec.type == 'NodePort':
            # Берём первый порт
            node_port = svc.spec.ports[0].node_port
            # Берём hostname из env, если хотим публичный доступ
            hostname = os.environ.get('NODE_HOST', 'localhost')
            url = f"http://{hostname}:{node_port}"
        # Если есть ClusterIP и мы внутри кластера, можно использовать напрямую
        elif svc.spec.type == 'ClusterIP':
            cluster_ip = svc.spec.cluster_ip
            port = svc.spec.ports[0].port
            url = f"http://{cluster_ip}:{port}"

        # Если есть ExternalName
        elif svc.spec.type == 'ExternalName':
            url = f"http://{svc.spec.external_name}"

        if url:
            buttons.append({
                "url": url,
                "label": f"{svc.metadata.namespace}/{svc.metadata.name}"
            })

    return buttons

@app.route('/')
def index():
    buttons = get_buttons()
    return render_template('index.html', buttons=buttons)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
