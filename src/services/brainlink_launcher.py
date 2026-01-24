"""BrainLinkClient launcher and connection checker"""

import os
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BrainLinkLauncher:
    """Service for finding, launching and connecting to BrainLinkClient"""
    
    CONFIG_FILE = "config/brainlink_path.json"
    
    def __init__(self):
        """Initialize launcher"""
        self.brainlink_path: Optional[Path] = None
        self.process: Optional[subprocess.Popen] = None
        self._found_memory_name: Optional[str] = None  # Cached memory name if found
        
        # Load saved path
        self._load_saved_path()
        
        logger.info("BrainLinkLauncher initialized")
    
    def _load_saved_path(self):
        """Load saved BrainLinkClient path"""
        config_path = Path(self.CONFIG_FILE)
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    path_str = data.get("brainlink_path")
                    if path_str:
                        path = Path(path_str)
                        if path.exists():
                            self.brainlink_path = path
                            logger.info(f"Loaded saved BrainLink path: {path}")
                        else:
                            logger.warning(f"Saved path doesn't exist: {path}")
            except Exception as e:
                logger.error(f"Error loading saved path: {e}")
    
    def _save_path(self, path: Path):
        """Save BrainLinkClient path"""
        config_path = Path(self.CONFIG_FILE)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"brainlink_path": str(path)}, f, indent=2)
            logger.info(f"Saved BrainLink path: {path}")
        except Exception as e:
            logger.error(f"Error saving path: {e}")
    
    def find_brainlink_client(self) -> Optional[Path]:
        """
        Find BrainLinkClient
        
        Returns:
            Path to BrainLinkClient directory or None
        """
        # If we already know the path, verify it exists and has main.py
        if self.brainlink_path:
            main_py = self.brainlink_path / "main.py"
            if self.brainlink_path.exists() and main_py.exists():
                logger.info(f"✅ Using saved BrainLink path: {self.brainlink_path}")
                return self.brainlink_path
            else:
                logger.warning(f"Saved path invalid: {self.brainlink_path}")
                self.brainlink_path = None  # Clear invalid path
        
        # Search in common locations
        search_paths = [
            Path(r"C:\Users\haqury\PycharmProjects\BrainLinkClient"),
            Path.home() / "PycharmProjects" / "BrainLinkClient",
            Path.home() / "Projects" / "BrainLinkClient",
            Path.cwd().parent / "BrainLinkClient",
        ]
        
        logger.info("Searching for BrainLinkClient...")
        
        for base_path in search_paths:
            main_py = base_path / "main.py"
            if main_py.exists():
                logger.info(f"✅ Found BrainLinkClient at: {base_path}")
                self.brainlink_path = base_path
                self._save_path(base_path)
                return base_path
        
        logger.warning("❌ BrainLinkClient not found in common locations")
        return None
    
    def is_process_running(self) -> bool:
        """
        Check if BrainLinkClient process is running
        
        Returns:
            True if process found, False otherwise
        """
        if not self.brainlink_path:
            return False
        
        try:
            import psutil
            main_py = str(self.brainlink_path / "main.py")
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if main_py in cmdline or 'BrainLinkClient' in cmdline:
                        logger.info(f"Found BrainLinkClient process: PID {proc.info['pid']}")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            logger.warning("psutil not available, cannot check processes")
        
        return False
    
    def is_shared_memory_running(self) -> bool:
        """
        Check if Shared Memory is available (BrainLinkClient with Shared Memory enabled)
        
        Returns:
            True if Shared Memory found, False otherwise
        """
        from multiprocessing import shared_memory
        
        # Try different possible names for Shared Memory
        possible_names = [
            "brainlink_data",      # Default name
            "BrainLinkData",       # Capitalized
            "brainlink",           # Short version
            "BrainLink",           # Capitalized short
            "brainlink_shm",       # With suffix
            "BrainLink_shm",       # Capitalized with suffix
            "psm_brainlink_data",  # Windows prefixed
        ]
        
        for memory_name in possible_names:
            try:
                shm = shared_memory.SharedMemory(name=memory_name)
                shm.close()
                logger.info(f"✅ Shared Memory found: '{memory_name}'")
                # Save the working name for later use
                self._found_memory_name = memory_name
                return True
            except FileNotFoundError:
                continue  # Try next name
            except Exception as e:
                logger.debug(f"Error checking memory name '{memory_name}': {e}")
                continue
        
        return False
    
    def is_running(self) -> bool:
        """
        Check if BrainLinkClient is running with Shared Memory enabled
        
        Returns:
            True if Shared Memory is available
        """
        if self.is_shared_memory_running():
            return True
        
        logger.info("❌ Shared Memory not found")
        return False
    
    def restart_with_shared_memory(self) -> bool:
        """
        Restart BrainLinkClient to enable Shared Memory
        
        Returns:
            True if restarted successfully
        """
        if not self.brainlink_path:
            logger.error("Cannot restart: path not set")
            return False
        
        logger.info("Restarting BrainLinkClient to enable Shared Memory...")
        
        # Try to kill existing process
        try:
            import psutil
            main_py = str(self.brainlink_path / "main.py")
            
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if main_py in cmdline or 'BrainLinkClient' in cmdline:
                        logger.info(f"Terminating existing BrainLinkClient process: PID {proc.info['pid']}")
                        proc.terminate()
                        proc.wait(timeout=3)  # Wait up to 3 seconds
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
        except ImportError:
            logger.warning("psutil not available, cannot kill existing process")
        except Exception as e:
            logger.warning(f"Error killing existing process: {e}")
        
        # Wait a bit for process to fully terminate
        time.sleep(1.0)
        
        # Launch new instance
        return self.launch()
    
    def launch(self, path: Optional[Path] = None) -> bool:
        """
        Launch BrainLinkClient
        
        Args:
            path: Optional path to BrainLinkClient directory
        
        Returns:
            True if launched successfully
        """
        # Use provided path or known path
        if path:
            self.brainlink_path = path
            self._save_path(path)
        
        if not self.brainlink_path:
            logger.error("Cannot launch: path not set")
            return False
        
        main_py = self.brainlink_path / "main.py"
        if not main_py.exists():
            logger.error(f"main.py not found at: {main_py}")
            return False
        
        try:
            # Launch BrainLinkClient
            logger.info(f"Launching BrainLinkClient from: {self.brainlink_path}")
            
            # Use pythonw to avoid showing console window
            python_exe = "pythonw" if os.name == 'nt' else "python3"
            
            self.process = subprocess.Popen(
                [python_exe, str(main_py)],
                cwd=str(self.brainlink_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info(f"✅ BrainLinkClient launched (PID: {self.process.pid})")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error launching BrainLinkClient: {e}")
            return False
    
    def wait_for_connection(self, timeout: float = 10.0) -> bool:
        """
        Wait for BrainLinkClient to start and create Shared Memory
        
        Args:
            timeout: Maximum time to wait (seconds)
        
        Returns:
            True if connected
        """
        import time
        
        logger.info(f"Waiting for BrainLink connection (timeout: {timeout}s)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_running():
                logger.info("✅ Connected to BrainLink!")
                return True
            time.sleep(0.5)
        
        logger.warning(f"❌ Connection timeout after {timeout}s")
        return False
    
    def cleanup(self):
        """Cleanup (don't kill BrainLinkClient process)"""
        # We don't kill the process - let it keep running
        pass
