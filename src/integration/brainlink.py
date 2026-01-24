"""
BrainLink integration via Shared Memory

Подключается к BrainLink Client и читает события для управления игроком.
"""

from multiprocessing import shared_memory
import struct
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# Event codes (must match BrainLink Client)
CODE_TO_EVENT = {
    0: "",
    1: "ml",    # Move Left
    2: "mr",    # Move Right
    3: "mu",    # Move Up
    4: "md",    # Move Down
    5: "stop",  # Stop
}

EVENT_TO_CODE = {v: k for k, v in CODE_TO_EVENT.items()}


class BrainLinkClient:
    """
    Ultra-fast BrainLink client using Shared Memory
    
    Reads player thoughts in real-time with ~0.01ms latency!
    """
    
    # Memory offsets (must match BrainLink Client)
    EVENT_CODE = 13  # offset for event code
    
    # Command fields (for sending events back to BrainLink)
    COMMAND_PENDING = 21
    COMMAND_TYPE = 22
    COMMAND_EVENT_CODE = 23
    COMMAND_TIMESTAMP = 24
    
    def __init__(self, memory_name: str = "brainlink_data"):
        """
        Initialize BrainLink client
        
        Args:
            memory_name: Name of shared memory (default: "brainlink_data")
        """
        self.memory_name = memory_name
        self.shm: Optional[shared_memory.SharedMemory] = None
        self.connected = False
        
        logger.info(f"BrainLink client initialized (memory: {memory_name})")
    
    def connect(self) -> bool:
        """
        Connect to BrainLink shared memory
        
        Returns:
            True if connected successfully
        """
        try:
            self.shm = shared_memory.SharedMemory(name=self.memory_name)
            self.connected = True
            logger.info(f"✅ Connected to BrainLink: '{self.memory_name}'")
            return True
        
        except FileNotFoundError:
            logger.warning(f"❌ BrainLink not found (memory: '{self.memory_name}')")
            logger.warning("   Make sure BrainLink Client is running with Shared Memory enabled!")
            self.connected = False
            return False
        
        except Exception as e:
            logger.error(f"❌ Error connecting to BrainLink: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from shared memory"""
        if self.shm:
            self.shm.close()
            self.shm = None
        self.connected = False
        logger.info("🛑 Disconnected from BrainLink")
    
    def _read_int(self, offset: int) -> int:
        """
        Read int32 from shared memory
        
        Args:
            offset: Field offset (in int32 units)
        
        Returns:
            Value as integer
        """
        if not self.shm:
            return 0
        
        byte_offset = offset * 4
        return struct.unpack('i', self.shm.buf[byte_offset:byte_offset + 4])[0]
    
    def _write_int(self, offset: int, value: int):
        """
        Write int32 to shared memory
        
        Args:
            offset: Field offset (in int32 units)
            value: Value to write
        """
        if not self.shm:
            return
        
        byte_offset = offset * 4
        self.shm.buf[byte_offset:byte_offset + 4] = struct.pack('i', value)
    
    def get_event(self) -> str:
        """
        Get current event from BrainLink (ultra-fast!)
        
        Returns:
            Event name: "ml", "mr", "mu", "md", "stop", or "" (no event)
        """
        if not self.connected:
            return ""
        
        try:
            event_code = self._read_int(self.EVENT_CODE)
            return CODE_TO_EVENT.get(event_code, "")
        except Exception as e:
            logger.error(f"Error reading event: {e}")
            return ""
    
    def is_connected(self) -> bool:
        """Check if connected to BrainLink"""
        return self.connected
    
    def send_event_to_history(self, event_name: str) -> bool:
        """
        Send event to BrainLink Client to save in history
        
        Args:
            event_name: Event name ("ml", "mr", "mu", "md", "stop")
        
        Returns:
            True if command sent successfully
        """
        if not self.connected:
            logger.warning("Cannot send event: not connected to BrainLink")
            return False
        
        try:
            import time
            
            # Convert event name to code
            event_code = EVENT_TO_CODE.get(event_name, 0)
            if event_code == 0:
                logger.warning(f"Unknown event name: {event_name}")
                return False
            
            # Check if previous command is still pending
            if self._read_int(self.COMMAND_PENDING) == 1:
                # Wait a bit for previous command to be processed
                time.sleep(0.001)  # 1ms
                if self._read_int(self.COMMAND_PENDING) == 1:
                    logger.debug("Previous command still pending, skipping")
                    return False
            
            # Write command
            timestamp = int(time.time() * 1000)  # milliseconds
            self._write_int(self.COMMAND_TYPE, 1)  # 1 = save to history
            self._write_int(self.COMMAND_EVENT_CODE, event_code)
            self._write_int(self.COMMAND_TIMESTAMP, timestamp)
            self._write_int(self.COMMAND_PENDING, 1)  # Mark as pending
            
            logger.debug(f"📤 Sent event to history: {event_name} (code: {event_code})")
            return True
            
        except Exception as e:
            logger.error(f"Error sending event to history: {e}")
            return False
    
    def send_event_for_ml_training(self, event_name: str) -> bool:
        """
        Send event to BrainLink Client for ML training
        
        Args:
            event_name: Event name ("ml", "mr", "mu", "md", "stop")
        
        Returns:
            True if command sent successfully
        """
        if not self.connected:
            logger.warning("Cannot send event: not connected to BrainLink")
            return False
        
        try:
            import time
            
            # Convert event name to code
            event_code = EVENT_TO_CODE.get(event_name, 0)
            if event_code == 0:
                logger.warning(f"Unknown event name: {event_name}")
                return False
            
            # Check if previous command is still pending
            if self._read_int(self.COMMAND_PENDING) == 1:
                # Wait a bit for previous command to be processed
                time.sleep(0.001)  # 1ms
                if self._read_int(self.COMMAND_PENDING) == 1:
                    logger.debug("Previous command still pending, skipping")
                    return False
            
            # Write command
            timestamp = int(time.time() * 1000)  # milliseconds
            self._write_int(self.COMMAND_TYPE, 2)  # 2 = save for ML training
            self._write_int(self.COMMAND_EVENT_CODE, event_code)
            self._write_int(self.COMMAND_TIMESTAMP, timestamp)
            self._write_int(self.COMMAND_PENDING, 1)  # Mark as pending
            
            logger.debug(f"🤖 Sent event for ML training: {event_name} (code: {event_code})")
            return True
            
        except Exception as e:
            logger.error(f"Error sending event for ML training: {e}")
            return False


# Singleton instance
_brainlink_instance: Optional[BrainLinkClient] = None


def get_brainlink_client(memory_name: str = "brainlink_data") -> BrainLinkClient:
    """
    Get singleton BrainLink client instance
    
    Args:
        memory_name: Name of shared memory
    
    Returns:
        BrainLink client instance
    """
    global _brainlink_instance
    
    # If instance exists but with different name, recreate it
    if _brainlink_instance is None or _brainlink_instance.memory_name != memory_name:
        if _brainlink_instance:
            _brainlink_instance.disconnect()
        _brainlink_instance = BrainLinkClient(memory_name)
    
    return _brainlink_instance
