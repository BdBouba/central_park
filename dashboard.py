import streamlit as st
from streamlit_autorefresh import st_autorefresh
import redis
import json
from datetime import datetime
import time

r = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)


st.set_page_config(page_title="Dashboard Monitoring", layout="wide")

# Rafraîchissement toutes les 2 secondes
st_autorefresh(interval=2000, key="refresh")

st.title("💻 Monitoring des machines en temps réel")
st.subheader("📡 Machines connectées")

def get_all_clients():
    keys = r.keys("client:*")
    clients = {}
    for key in keys:
        data_raw = r.get(key)
        if data_raw:
            identifier = key.split(":")[1]
            data = json.loads(data_raw)
            clients[identifier] = data
    return clients

clients = get_all_clients()

if not clients:
    st.info("Aucune machine n'est connectée pour le moment.")
else:
    for identifier, data in clients.items():
        st.markdown(f"### 🖥 Machine `{identifier}`")

        col1, col2, col3 = st.columns(3)
        col1.metric("CPU", f"{data['cpu_total']}%")
        col2.metric("RAM", f"{data['memory_percent']}%")
        col3.metric("Processus", f"{data['process_count']}")

        last_update = datetime.fromtimestamp(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        st.text(f"🕒 Dernière mise à jour : {last_update}")
        st.text(f"🖥 Cœurs CPU : {len(data['cpu_per_core'])} (par cœur : {', '.join(map(str, data['cpu_per_core']))})")
        st.text(f"💾 Mémoire : {data['memory_percent']}% | Échange : {data['swap_percent']}%")
        st.text(f"💽 Disque : {data['disk_percent']}%")
        st.text(f"📅 Démarrage : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['system']['boot_time']))}")
        st.text(f"📊 Réseau : ↑ {data['bytes_sent']} o | ↓ {data['bytes_recv']} o")
        st.text(f"🧠 OS : {data['system']['platform']} {data['system']['platform_version']}")
        st.markdown("---")
        st.text("Voici les données brutes reçues de la machine :")
        st.json(data)
        st.markdown("---")
st.text("Les données sont stockées dans Redis sous la clé `client:<identifier>`.")