import time
from .core import Node

class OptimizedNode(Node):

    def __init__(self, name, network_key):
        
        self._cached_peers = {}
        self._last_peer_refresh = 0
        self._refresh_interval = 10 
        super().__init__(name, network_key) 
    
    def _load_peers(self):

        current_time = time.time()
        if current_time - self._last_peer_refresh > self._refresh_interval:
            super()._load_peers() 
            
            self._cached_peers = self.known_peers.copy()
            self._last_peer_refresh = current_time
        else:

            self.known_peers = self._cached_peers

    def get_peer_key(self, node_id):

        self._load_peers()
        return self.known_peers.get(node_id)