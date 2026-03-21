import time
from collections import defaultdict

class WindowManager:
    def __init__(self, window_size=60):
        self.window_size = window_size
        self.buffer = defaultdict(list)
        self.start_time = time.time()

    def add_event(self, event):
        self.buffer[event["endpoint_id"]].append(event)

    def should_flush(self):
        return time.time() - self.start_time >= self.window_size

    def flush(self):
        # Create a shallow copy to return
        data = dict(self.buffer)
        
        # Clear buffer to prevent memory leaks and reset window
        self.buffer.clear()
        self.start_time = time.time()
        
        return data
