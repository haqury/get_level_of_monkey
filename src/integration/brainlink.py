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
        
        try:
            byte_offset = offset * 4
            value = struct.unpack('i', self.shm.buf[byte_offset:byte_offset + 4])[0]
            return value
        except Exception as e:
            logger.error(f"Error reading int from shared memory (offset={offset}): {e}", exc_info=True)
            return 0
    
    def _write_int(self, offset: int, value: int):
        """
        Write int32 to shared memory
        
        Args:
            offset: Field offset (in int32 units)
            value: Value to write (will be clamped to int32 range if needed)
        """
        if not self.shm:
            return
        
        # Clamp value to int32 range to prevent "argument out of range" error
        # int32 range: -2,147,483,648 to 2,147,483,647
        INT32_MAX = 2147483647
        INT32_MIN = -2147483648
        
        if value > INT32_MAX:
            logger.warning(f"Value {value} exceeds int32 max, clamping to {INT32_MAX}")
            value = INT32_MAX
        elif value < INT32_MIN:
            logger.warning(f"Value {value} below int32 min, clamping to {INT32_MIN}")
            value = INT32_MIN
        
        byte_offset = offset * 4
        self.shm.buf[byte_offset:byte_offset + 4] = struct.pack('i', value)
    
    def get_event(self) -> str:
        """
        Get current event from BrainLink (ultra-fast!)
        
        Returns:
            Event name: "ml", "mr", "mu", "md", "stop", or "" (no event)
        """
        if not self.connected:
            # Log disconnection periodically
            if not hasattr(self, '_disconnect_log_counter'):
                self._disconnect_log_counter = 0
            self._disconnect_log_counter += 1
            if self._disconnect_log_counter % 300 == 0:  # Log every 5 seconds at 60fps
                logger.warning(f"🎮 BrainLink: Not connected (counter: {self._disconnect_log_counter})")
            return ""
        
        try:
            event_code = self._read_int(self.EVENT_CODE)
            event_name = CODE_TO_EVENT.get(event_code, "")
            
            # Log event changes for debugging (only occasionally to avoid spam)
            if not hasattr(self, '_last_logged_event'):
                self._last_logged_event = ""
                self._event_log_counter = 0
                self._empty_read_counter = 0
                logger.info(f"🎮 BrainLink: Starting to read events from shared memory (memory_name: {self.memory_name})")
                # Log first read to verify connection
                logger.info(f"🎮 BrainLink: First read - event_code={event_code}, event_name='{event_name}'")
            
            self._event_log_counter += 1
            if event_name != self._last_logged_event:
                if event_code != 0:  # Only log non-empty events
                    logger.info(f"🎮 Game read event: {event_name} (code: {event_code})")
                elif event_name == "" and self._last_logged_event != "":
                    logger.info(f"🎮 Game: Event cleared (was: '{self._last_logged_event}')")
                self._last_logged_event = event_name
            elif self._event_log_counter % 100 == 0 and event_code != 0:  # Log every 100 reads
                logger.info(f"🎮 Game reading event: {event_name} (code: {event_code}) - still active")
            elif self._event_log_counter == 10:  # Log 10th read to verify we're reading
                logger.info(f"🎮 BrainLink: 10th read - event_code={event_code}, event_name='{event_name}'")
            
            # Log if we're consistently getting empty events (periodically)
            if event_code == 0 or event_name == "":
                self._empty_read_counter += 1
                if self._empty_read_counter == 1:  # Log first empty read
                    logger.info(f"🎮 BrainLink: Reading event_code=0 (empty) - waiting for events...")
                elif self._empty_read_counter == 60:  # Log after 1 second at 60fps
                    logger.info(f"🎮 BrainLink: Still reading event_code=0 (empty) after 1 second (counter: {self._empty_read_counter})")
                elif self._empty_read_counter % 300 == 0:  # Log every 5 seconds at 60fps
                    logger.info(f"🎮 BrainLink: Reading event_code=0 (empty) consistently (counter: {self._empty_read_counter})")
            else:
                if self._empty_read_counter > 0:
                    logger.info(f"🎮 BrainLink: Event received after {self._empty_read_counter} empty reads: {event_name} (code: {event_code})")
                self._empty_read_counter = 0
            
            return event_name
        except Exception as e:
            logger.error(f"Error reading event: {e}", exc_info=True)
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
            # Use relative timestamp (milliseconds since game start) to avoid int32 overflow
            # Absolute timestamp would be too large for int32
            if not hasattr(self, '_start_time'):
                self._start_time = time.time()
            relative_timestamp = int((time.time() - self._start_time) * 1000)  # milliseconds since start
            
            self._write_int(self.COMMAND_TYPE, 1)  # 1 = save to history
            self._write_int(self.COMMAND_EVENT_CODE, event_code)
            self._write_int(self.COMMAND_TIMESTAMP, relative_timestamp)
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
            # Use relative timestamp (milliseconds since game start) to avoid int32 overflow
            # Absolute timestamp would be too large for int32
            if not hasattr(self, '_start_time'):
                self._start_time = time.time()
            relative_timestamp = int((time.time() - self._start_time) * 1000)  # milliseconds since start
            
            self._write_int(self.COMMAND_TYPE, 2)  # 2 = save for ML training
            self._write_int(self.COMMAND_EVENT_CODE, event_code)
            self._write_int(self.COMMAND_TIMESTAMP, relative_timestamp)
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
