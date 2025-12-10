import json
import base64
import os
import time
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization
from pydantic import BaseModel

class DataPacket(BaseModel):
    sender_id: str
    timestamp: str 
    encrypted_payload: str
    signature: str
    
    def to_json(self):
        return self.model_dump_json()

class CryptoVault:
    def __init__(self, node_name: str, network_key: bytes):
        self.node_name = node_name
        self.network_key = network_key
        self.cipher = Fernet(self.network_key)
        self.keys_dir = "keys"
        
        self._peer_key_cache = {} 
        
        os.makedirs(self.keys_dir, exist_ok=True)
        self._private_key, self.public_key = self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        priv_path = f"{self.keys_dir}/{self.node_name}_private.pem"
        pub_path = f"{self.keys_dir}/{self.node_name}_public.pem"

        if os.path.exists(priv_path) and os.path.exists(pub_path):
            try:
                with open(priv_path, "rb") as f:
                    priv = serialization.load_pem_private_key(f.read(), password=None)
                with open(pub_path, "rb") as f:
                    pub = serialization.load_pem_public_key(f.read())
                return priv, pub
            except Exception:
                pass 

        priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pub = priv.public_key()
        
        with open(priv_path, "wb") as f:
            f.write(priv.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(pub_path, "wb") as f:
            f.write(pub.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        return priv, pub

    def get_public_key_str(self) -> str:
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')

    def encrypt_payload(self, raw_data: dict) -> str:
        json_str = json.dumps(raw_data)
        return self.cipher.encrypt(json_str.encode('utf-8')).decode('utf-8')

    def decrypt_payload(self, encrypted_str: str) -> dict:
        try:
            return json.loads(self.cipher.decrypt(encrypted_str.encode('utf-8')).decode('utf-8'))
        except Exception:
            return None

    def sign_message(self, message_str: str) -> str:
        signature = self._private_key.sign(
            message_str.encode('utf-8'),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

    def get_peer_public_key(self, sender_id: str, sender_pub_pem: str):

        if sender_id in self._peer_key_cache:
            return self._peer_key_cache[sender_id]
        
        try:
            pub_key = serialization.load_pem_public_key(sender_pub_pem.encode('utf-8'))
            self._peer_key_cache[sender_id] = pub_key
            return pub_key
        except Exception:
            return None

    def verify_signature(self, message_str: str, signature_str: str, sender_id: str, sender_public_key_pem: str) -> bool:
        try:
            sender_pub_key = self.get_peer_public_key(sender_id, sender_public_key_pem)
            if not sender_pub_key: return False

            sender_pub_key.verify(
                base64.b64decode(signature_str),
                message_str.encode('utf-8'),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

class Node:
    def __init__(self, name: str, network_key: bytes):
        self.name = name
        self.vault = CryptoVault(name, network_key)
        self.known_peers = {} 

    def is_timestamp_valid(self, timestamp_str: str) -> bool:
    
        try:
            pkt_time = float(timestamp_str)
            current_time = time.time()
            
            if abs(current_time - pkt_time) > 10.0:
                return False
            return True
        except:
            return False