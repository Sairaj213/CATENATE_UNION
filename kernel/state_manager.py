import streamlit as st
import threading
from collections import deque
from datetime import datetime
from cryptography.fernet import Fernet
from protocols.network_extensions import OptimizedNode

class SimulationState:
    def __init__(self):
        
        self.lock = threading.Lock()

        self.network_key = Fernet.generate_key()
        
        self.packet_queue = None 
        import queue
        self.packet_queue = queue.Queue()
        
        self.nodes = {}       
        
        self.logs = deque(maxlen=50)
        
        self.active_links = [] 
        self.is_running = False

        self.hub_node = OptimizedNode("CENTRAL_HUB", self.network_key)

        self.speed_mod = 1.0
        self.hack_prob = 0.0
        self.jitter = 0.0
        self.packet_types = ["INTEL", "BIO", "CHAT", "CRYPTO"]
        self.auto_revive = False

        self.max_range = 15.0       
        self.batt_drain_mod = 1.0   
        self.strict_replay = True   

    def log(self, type_, content, status, sender):
        
        entry = {
            "Time": datetime.now().strftime("%H:%M:%S"),
            "ID": sender,
            "Type": type_,
            "Payload": content,
            "Status": status
        }
        with self.lock:
            self.logs.appendleft(entry)

@st.cache_resource
def get_state():
    return SimulationState()