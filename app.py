import streamlit as st
import time
import math
import random
from kernel.state_manager import get_state
from kernel.simulation_engine import BotThread, start_hub_listener
from interface.ui_components import CYBERPUNK_CSS, render_radar_graph, style_log_dataframe

st.set_page_config(
    page_title="Crisscross: Lattice Network Monitor",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)

STATE = get_state()
start_hub_listener()

st.sidebar.header("🕹️ COMMAND PROTOCOLS")

if st.sidebar.button("🔴 STOP SYSTEM" if STATE.is_running else "🟢 INITIALIZE SYSTEM"):
    STATE.is_running = not STATE.is_running

st.sidebar.subheader("Global Tuning")
STATE.speed_mod = st.sidebar.slider("Clock Speed (Hz)", 0.1, 5.0, 1.0)
STATE.hack_prob = st.sidebar.slider("Network Entropy (Hacking %)", 0.0, 1.0, 0.0)
STATE.jitter = st.sidebar.slider("Signal Jitter (Latency)", 0.0, 2.0, 0.0)

st.sidebar.subheader("Physics & Hardware")
STATE.max_range = st.sidebar.slider("Signal Horizon (Range)", 5.0, 30.0, 15.0)
STATE.batt_drain_mod = st.sidebar.slider("Battery Drain Rate", 0.1, 5.0, 1.0)

STATE.packet_types = st.sidebar.multiselect(
    "Allowed Protocols", 
    ["INTEL", "BIO", "CHAT", "CRYPTO"], 
    default=["INTEL", "BIO", "CHAT", "CRYPTO"]
)
STATE.auto_revive = st.sidebar.checkbox("Auto-Revive Protocol", value=False)

st.sidebar.subheader("Deployment")
n_count = st.sidebar.number_input("Unit Count", 1, 50, 8)

if st.sidebar.button("DEPLOY UNITS"):
    with STATE.lock:
        current_count = len(STATE.nodes)
        for i in range(current_count, n_count):
            nid = f"Unit-{i+1:02d}"

            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(2, STATE.max_range * 0.8)
            x, y = radius * math.cos(angle), radius * math.sin(angle)

            bot = BotThread(nid, x, y)
            STATE.nodes[nid] = bot
            bot.start()

st.title("🛡️ CATENATE UNION")

c1, c2, c3, c4 = st.columns(4)

with STATE.lock:
    active_count = sum(1 for n in STATE.nodes.values() if n.alive)
    total_nodes = max(1, len(STATE.nodes))
    nodes_snapshot = STATE.nodes.copy()

c1.metric("NETWORK INTEGRITY", f"{int((active_count/total_nodes)*100)}%")
c2.metric("PACKET QUEUE", STATE.packet_queue.qsize())
c3.metric("ENTROPY LEVEL", f"{int(STATE.hack_prob * 100)}%")
c4.metric("SYSTEM STATUS", "ONLINE" if STATE.is_running else "STANDBY")

col_graph, col_controls = st.columns([3, 1])

with col_graph:
    fig = render_radar_graph(nodes_snapshot, STATE.max_range)
    st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

with col_controls:
    st.subheader("📡 Unit Inspector")
    if nodes_snapshot:
        sel_id = st.selectbox("Select Unit", list(nodes_snapshot.keys()))
        unit = nodes_snapshot[sel_id]

        st.markdown(f"""
        **ID:** `{unit.node_id}`  
        **STATUS:** `{'ALIVE' if unit.alive else 'KIA'}`  
        **COORDS:** `{unit.x:.2f}, {unit.y:.2f}`
        """)
        
        batt_val = int(max(0, unit.battery))
        
        bar_color = "red" if batt_val < 20 else "green"
        st.progress(batt_val, text=f"Battery: {batt_val}%")

        c_kill, c_chg = st.columns(2)
        if c_kill.button("💀 TERMINATE"): 
            unit.alive = False
        if c_chg.button("⚡ RECHARGE"): 
            unit.alive = True
            unit.battery = 100.0
            
        unit.is_compromised = st.toggle("Compromise Protocol", value=unit.is_compromised)
    else:
        st.info("No Units Deployed")

st.subheader("🖥️ DECRYPTED NETWORK TRAFFIC")

if STATE.logs:
    with STATE.lock:
        logs_snapshot = list(STATE.logs)
    
    styled_df = style_log_dataframe(logs_snapshot)
    st.dataframe(
        styled_df, 
        use_container_width=True, 
        height=250,
        hide_index=True
    )

if STATE.is_running:
    time.sleep(0.8)
    st.rerun()