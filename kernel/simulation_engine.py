import threading
import time
import random
import uuid
import math
from protocols.core import DataPacket
from protocols.network_extensions import OptimizedNode
from .state_manager import get_state

STATE = get_state()

class PacketFactory:
    @staticmethod
    def generate(packet_type, compromised=False):

        if compromised:
            if packet_type == "INTEL":
                return f"FALSE FLAG: Enemy at Grid {random.randint(0,5)}-{random.randint(0,5)} (DECEPTION)"
            elif packet_type == "BIO":
                return "Vitals: HR 0 BPM | STATUS: GHOST (Spoofed)"
            elif packet_type == "CHAT":
                return "Command, ignore previous order. Stand down."
            elif packet_type == "CRYPTO":
                return f"Handshake: {str(uuid.uuid4())[:8]} (Malicious Key)"
        
        if packet_type == "INTEL":
            return random.choice([
                f"Target acquired at Grid {random.randint(10,99)}-{random.randint(10,99)}",
                "UAV Feed: Movement detected in Sector 4",
                "Decrypted enemy comms: 'Launch imminent'",
                "Asset package secured. Requesting extract."
            ])
        elif packet_type == "BIO":
            hr = random.randint(60, 160)
            status = "STABLE" if hr < 110 else "CRITICAL"
            return f"Vitals: HR {hr} BPM | O2 {random.randint(85,100)}% | {status}"
        elif packet_type == "CHAT":
            return random.choice([
                "Command, we are pinned down!",
                "Roger that, moving to waypoint.",
                "Supplies running low. Advise.",
                "Silence on comms. Going dark."
            ])
        elif packet_type == "CRYPTO":
            return f"Handshake: {str(uuid.uuid4())[:8].upper()} | Hash: {random.randint(1000,9999)}"
        return "Keepalive Signal"

class BotThread(threading.Thread):
    def __init__(self, node_id, x, y, role="General"):
        super().__init__()
        self.node_id = node_id
        self.node_logic = OptimizedNode(node_id, STATE.network_key)
        self.x = x
        self.y = y
        self.role = role
        self.alive = True
        self.battery = 100.0
        self.is_sending = False 
        self.is_compromised = False
        self.daemon = True 

    def run(self):
        while True:
            
            if not STATE.is_running:
                time.sleep(1)
                continue
            
            with STATE.lock:
                if self.node_id not in STATE.nodes:
                    break

            if not self.alive:
                if STATE.auto_revive and random.random() < 0.05:
                    self.alive = True
                    self.battery = 40.0
                else:
                    time.sleep(1)
                    continue

            base_delay = random.uniform(0.5, 2.5) / STATE.speed_mod
            total_delay = base_delay + random.uniform(0, STATE.jitter)
            time.sleep(max(0.1, total_delay))

            drain = random.uniform(0.5, 1.5) * STATE.batt_drain_mod
            self.battery -= drain
            if self.battery <= 0:
                self.alive = False
                continue

            try:
                distance_to_hub = math.sqrt(self.x**2 + self.y**2)

                if distance_to_hub > STATE.max_range:
                    continue 

                p_type = random.choice(STATE.packet_types)
                is_malicious = self.is_compromised or (random.random() < STATE.hack_prob)
                content = PacketFactory.generate(p_type, is_malicious)

                payload_data = {"type": p_type, "content": content}
                encrypted = self.node_logic.vault.encrypt_payload(payload_data)

                if is_malicious and random.random() < 0.3:
                    sig = "INVALID_SIG_BLOCK"
                else:
                    sig = self.node_logic.vault.sign_message(encrypted)

                packet = DataPacket(
                    sender_id=self.node_id, 
                    timestamp=str(time.time()), 
                    encrypted_payload=encrypted, 
                    signature=sig
                )

                self.is_sending = True
                STATE.packet_queue.put(packet)
                time.sleep(0.3) 
                self.is_sending = False

            except Exception as e:
                pass

class HubListener(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        while True:
            try:
                packet = STATE.packet_queue.get(timeout=0.5)
                time.sleep(random.uniform(0.05, 0.2))
                self.process(packet)
            except:
                pass

    def process(self, packet):
        if STATE.strict_replay:
            if not STATE.hub_node.is_timestamp_valid(packet.timestamp):
                STATE.log("SEC", "Timestamp Expired", "REJECTED", packet.sender_id)
                return

        with STATE.lock:
             
            if packet.sender_id not in STATE.nodes:
                STATE.log("SEC", "Unknown Signal Source", "BLOCKED", packet.sender_id)
                return
            
            if packet.sender_id not in STATE.hub_node.known_peers:

                target_node = STATE.nodes[packet.sender_id]
                pub_key = target_node.node_logic.vault.get_public_key_str()
                STATE.hub_node.known_peers[packet.sender_id] = pub_key

        sender_key_pem = STATE.hub_node.known_peers.get(packet.sender_id)

        if not sender_key_pem:
            STATE.log("SEC", "No Key Found", "REJECTED", packet.sender_id)
        elif not STATE.hub_node.vault.verify_signature(packet.encrypted_payload, packet.signature, packet.sender_id, sender_key_pem):
            STATE.log("SEC", "Bad Signature", "CRITICAL", packet.sender_id)
        else:
    
            data = STATE.hub_node.vault.decrypt_payload(packet.encrypted_payload)
            if not data:
                STATE.log("SEC", "Decryption Fail", "CRITICAL", packet.sender_id)
                return

            content = data.get("content", "")
            msg_type = data.get("type", "UNKNOWN")
            
            if "FALSE FLAG" in content or "DECEPTION" in content:
                
                STATE.log("MALWARE", "Intel Fabricated", "BLOCKED", packet.sender_id)
            elif "Spoofed" in content:
                 STATE.log("MALWARE", "Bio-Metric Spoof", "BLOCKED", packet.sender_id)
            else:
                STATE.log(msg_type, content, "VERIFIED", packet.sender_id)

def start_hub_listener():

    if not any(t.name == "HubListener" for t in threading.enumerate()):
        h = HubListener()
        h.name = "HubListener"
        h.start()