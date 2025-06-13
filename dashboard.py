import streamlit as st
from streamlit_autorefresh import st_autorefresh
import redis
import json
from datetime import datetime
import time

# Fonction pour formater les octets en format lisible (KB, MB, GB, etc.)
def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    units = ["o", "Ko", "Mo", "Go", "To"]
    while size >= power and n < len(units)-1:
        size /= power
        n += 1
    return f"{size:.2f} {units[n]}"

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
        col1.metric("💻 CPU Total", f"{data['cpu_total']}%")
        col2.metric("🧠 RAM", f"{data['memory_percent']}%")
        col3.metric("⚙️ Processus", f"{data['process_count']}")

        last_update = datetime.fromtimestamp(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        st.write(f"🕒 **Dernière mise à jour :** {last_update}")

        st.write(f"🖥 **Cœurs CPU :** {len(data['cpu_per_core'])} (par cœur : {', '.join(f'{x}%' for x in data['cpu_per_core'])})")
        st.write(f"💾 **Mémoire utilisée :** {data['memory_percent']}% | **Swap :** {data['swap_percent']}%")
        st.write(f"💽 **Utilisation disque :** {data['disk_percent']}%")
        st.write(f"📅 **Démarrage système :** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['system']['boot_time']))}")
        st.write(f"📊 **Réseau :** ↑ {format_bytes(data['bytes_sent'])} | ↓ {format_bytes(data['bytes_recv'])}")
        st.write(f"🧠 **OS :** {data['system']['platform']} {data['system']['platform_version']}")

        st.markdown("---")
        st.write("### Données brutes reçues :")
        st.json(data)
        st.markdown("---")

st.text("Les données sont stockées dans Redis sous la clé `client:<identifier>`.")
