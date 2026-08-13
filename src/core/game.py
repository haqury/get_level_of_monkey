"""Main Game class"""

import json
import logging
from pathlib import Path
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData, TextFont, Filename, WindowProperties, OrthographicLens

from src.core.input_manager import (
    InputManager,
    MOVEMENT_SOURCE_KEYBOARD,
    MOVEMENT_SOURCE_BRAINLINK,
)
from src.core.scene_manager import SceneManager
from src.systems.energy_system import EnergySystem
from src.systems.health_system import HealthSystem
from src.systems.progression_system import ProgressionSystem
from src.entities.player import Player
from src.scenes.cave import CaveScene
from src.scenes.kitchen import KitchenScene
from src.scenes.minigame import MinigameScene
from src.scenes.main_menu import MainMenuScene
from src.ui.hud import HUD
from src.ui.dialog_box import DialogBox
from src.ui.pause_menu import PauseMenu
from src.services.brainlink_launcher import BrainLinkLauncher
from src.services.save_system import SaveSystem
from src.core.i18n import load_locale, t, resolve_dialog

logger = logging.getLogger(__name__)


class Game(ShowBase):
    """Main game class"""
    
    def __init__(self):
        # Load config (renamed to avoid conflict with ShowBase.config)
        self.game_config = self._load_config()
        self.balance = self._load_balance()
        load_locale(self.game_config.get("locale", "en"))
        
        # Configure Panda3D
        self._configure_panda3d()
        
        # Initialize ShowBase
        super().__init__()
        
        logger.info("🎮 Fucking Pickup - Initializing...")
        
        # Setup window
        self._setup_window()
        
        # Setup font with Cyrillic support
        self._setup_font()
        
        # Initialize systems
        self.input_manager = InputManager(
            self,
            brainlink_enabled=self.game_config["brainlink"]["enabled"]
        )
        
        self.energy_system = EnergySystem(
            max_energy=self.game_config["player"]["initial_energy"],
            regen_rate=self.game_config["player"]["energy_regen_rate"]
        )
        # Set cheater mode if enabled in config
        if self.game_config["player"].get("cheater_mode", False):
            self.energy_system.cheater_mode = True
        
        self.health_system = HealthSystem(
            max_hp=self.game_config["player"]["initial_hp"]
        )
        
        # Progression system
        self.progression_system = ProgressionSystem(self.balance.get("progression", {}))
        self.progression_system.on_level_up = self._on_level_up
        
        # Player
        self.player = Player(self, pos=(0, 0))
        self.player_speed = self.game_config["player"]["move_speed"]
        self.move_cost = self.game_config["player"]["move_cost"]
        
        # Apply initial upgrades (if any from saved game)
        self._apply_upgrades()
        
        # UI
        self.hud = HUD(self)
        self.dialog_box = DialogBox(self)
        self.pause_menu = PauseMenu(self)
        self.on_pause_restart = self._on_pause_restart
        self.on_pause_load = self._on_pause_load
        self.on_pause_settings = self._on_pause_settings
        self.on_pause_exit = self._on_pause_exit
        
        # ESC opens pause menu — bound in InputManager and calls self._on_escape
        
        # BrainLink launcher
        self.brainlink_launcher = BrainLinkLauncher()
        
        # Save system
        self.save_system = SaveSystem()
        
        # Scene management
        self.scene_manager = SceneManager(self)
        self._setup_scenes()
        
        # Game state
        self.current_npc = None  # NPC player is interacting with
        self.in_game = False  # Track if we're in game or menu
        self._just_started_game = False  # Track if we just started game (for gray screen fix)
        self._start_frame_count = 0  # Count frames after game start
        self._exit_dialog_shown = False  # Track if exit dialog was already shown
        
        # Input callbacks
        self.input_manager.on_action = self.on_action_pressed
        self.input_manager.on_sit_pause = self._on_sit_pause
        
        # Setup game loop
        self.taskMgr.add(self.update, "game_update")
        
        # Start in main menu
        self.hud.hide()  # Hide HUD in menu
        self.scene_manager.switch_to("main_menu", self.player)
        
        # Check BrainLink status after a short delay
        self.taskMgr.doMethodLater(1.0, self._check_brainlink_startup, "check_brainlink")
        
        logger.info("✅ Game initialized successfully!")
        logger.info("🎮 Controls:")
        logger.info("   Keyboard: Arrow keys to move, Space for action/dialog")
        logger.info("   BrainLink: Think ml/mr/mu/md to move!")
        logger.info("")
        logger.info("📍 Starting in Main Menu")
    
    def _load_config(self) -> dict:
        """Load game configuration"""
        config_path = Path("config/game_config.json")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.warning("Config not found, using defaults")
            return self._get_default_config()
    
    def _load_balance(self) -> dict:
        """Load balance configuration"""
        balance_path = Path("config/balance.json")
        if balance_path.exists():
            with open(balance_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.warning("Balance config not found")
            return {"minigame": {}, "progression": {}}
    
    def _get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            "window": {"title": "Fucking Pickup", "width": 1920, "height": 1080, "fullscreen": True, "fps": 60},
            "player": {"name": "Player", "initial_hp": 3, "initial_energy": 100, "energy_regen_rate": 5.0, "move_cost": 100, "move_speed": 5},
            "brainlink": {"enabled": True, "memory_name": "brainlink_data", "check_interval": 0.016, "send_keyboard_events": True, "send_to_history": True, "send_to_ml": False, "confidence_threshold": 0.5, "min_confidence": 0.25, "full_confidence": 0.7, "prediction_weights": [1.0, 1.0, 1.0, 1.0], "model_path": ""},
            "controls": {"keyboard": {"up": "arrow_up", "down": "arrow_down", "left": "arrow_left", "right": "arrow_right", "action": "space", "sit_pause": "p"}},
            "locale": "en",
        }
    
    def _configure_panda3d(self):
        """Configure Panda3D settings"""
        cfg = self.game_config["window"]
        
        loadPrcFileData("", f"window-title {cfg['title']}")
        
        # Always set window size explicitly, even in fullscreen
        # This ensures the correct resolution is used
        width = cfg.get('width', 1920)
        height = cfg.get('height', 1080)
        loadPrcFileData("", f"win-size {width} {height}")
        
        # Set fullscreen mode
        if cfg.get('fullscreen', False):
            loadPrcFileData("", "fullscreen #t")
        else:
            loadPrcFileData("", "fullscreen #f")
        
        loadPrcFileData("", "framebuffer-multisample 1")
        loadPrcFileData("", "multisamples 2")
        loadPrcFileData("", f"sync-video {'#t' if cfg['fps'] == 60 else '#f'}")
        # Enable UTF-8 text encoding for Unicode support (Cyrillic, emoji, etc.)
        loadPrcFileData("", "text-encoding utf8")
        try:
            loadPrcFileData("", "text-use-harfbuzz #t")
        except:
            pass  # HarfBuzz may not be available

    # === Window / display ===
    def _get_native_display_size(self) -> tuple[int, int]:
        """Native monitor resolution (for fullscreen without OS scaling)."""
        try:
            if self.pipe:
                w = int(self.pipe.getDisplayWidth())
                h = int(self.pipe.getDisplayHeight())
                if w > 0 and h > 0:
                    return w, h
        except Exception as e:
            logger.warning("Could not query native display size: %s", e)
        cfg = self.game_config.get("window", {})
        return int(cfg.get("width", 1920)), int(cfg.get("height", 1080))

    def _get_window_pixel_size(self) -> tuple[int, int]:
        """Current framebuffer size in pixels."""
        try:
            props = self.win.getProperties()
            w = int(props.getXSize())
            h = int(props.getYSize())
            if w > 0 and h > 0:
                return w, h
        except Exception:
            pass
        cfg = self.game_config.get("window", {})
        return int(cfg.get("width", 1920)), int(cfg.get("height", 1080))

    def _resolve_window_size(self, width: int, height: int, fullscreen: bool) -> tuple[int, int]:
        """Pick final window size; fullscreen uses native monitor resolution."""
        if fullscreen:
            return self._get_native_display_size()
        return int(width), int(height)

    def _schedule_camera_aspect_update(self) -> None:
        """Update camera after window size has settled."""
        self.taskMgr.remove("update_camera_aspect")
        self.taskMgr.doMethodLater(0.1, self._delayed_camera_setup, "update_camera_aspect")

    def _on_window_event(self, window) -> None:
        """Keep camera aspect in sync when the OS window is resized."""
        if window is not self.win:
            return
        self._schedule_camera_aspect_update()

    def _apply_window_properties(self, width: int, height: int, fullscreen: bool) -> tuple[int, int]:
        """Apply size/fullscreen to the OS window. Returns actual requested size."""
        resolved_w, resolved_h = self._resolve_window_size(width, height, fullscreen)
        props = WindowProperties()
        props.setSize(resolved_w, resolved_h)
        props.setFullscreen(bool(fullscreen))
        self.win.requestProperties(props)
        logger.info(
            "Window properties requested: %sx%s, fullscreen=%s (config was %sx%s)",
            resolved_w, resolved_h, fullscreen, width, height,
        )
        return resolved_w, resolved_h

    def _sync_window_config(self, width: int, height: int, fullscreen: bool) -> None:
        """Persist effective window settings to memory and disk."""
        window_cfg = self.game_config.get("window", {})
        window_cfg["width"] = int(width)
        window_cfg["height"] = int(height)
        window_cfg["fullscreen"] = bool(fullscreen)
        self.game_config["window"] = window_cfg
        try:
            config_path = Path("config/game_config.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.game_config, f, indent=2)
            logger.info("Saved window config: %sx%s fullscreen=%s", width, height, fullscreen)
        except Exception as e:
            logger.warning("Failed to save window config: %s", e)

    def apply_resolution(self, width: int, height: int, fullscreen: bool) -> None:
        """
        Apply new resolution/fullscreen settings at runtime and persist to config.

        In fullscreen mode the native monitor resolution is used to avoid stretching.
        """
        logger.info("Applying resolution: %sx%s, fullscreen=%s", width, height, fullscreen)
        try:
            applied_w, applied_h = self._apply_window_properties(width, height, fullscreen)
            self._sync_window_config(applied_w, applied_h, fullscreen)
            self._schedule_camera_aspect_update()
        except Exception as e:
            logger.error("Failed to apply window properties: %s", e)

    def get_window_display_info(self) -> str:
        """Human-readable current window mode for settings UI."""
        w, h = self._get_window_pixel_size()
        fullscreen = False
        try:
            fullscreen = bool(self.win.getProperties().getFullscreen())
        except Exception:
            fullscreen = bool(self.game_config.get("window", {}).get("fullscreen", False))
        mode = t("settings.fullscreen_mode") if fullscreen else t("settings.windowed_mode")
        return t("settings.display_format", w=w, h=h, mode=mode)
    
    def set_locale(self, locale: str) -> None:
        """Switch UI language and persist to config."""
        from src.core.i18n import SUPPORTED_LOCALES
        if locale not in SUPPORTED_LOCALES:
            return
        self.game_config["locale"] = locale
        load_locale(locale)
        try:
            config_path = Path("config/game_config.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {}
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            config["locale"] = locale
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save locale: %s", e)
        self.refresh_ui_locale()
    
    def refresh_ui_locale(self) -> None:
        """Refresh all visible UI strings after language change."""
        menu = self.scene_manager.loaded_scenes.get("main_menu")
        if menu and hasattr(menu, "refresh_locale"):
            menu.refresh_locale()
        if self.pause_menu and hasattr(self.pause_menu, "refresh_locale"):
            self.pause_menu.refresh_locale()
        if self.hud and hasattr(self.hud, "refresh_locale"):
            self.hud.refresh_locale()
        if self.dialog_box and hasattr(self.dialog_box, "refresh_locale"):
            self.dialog_box.refresh_locale()
        for scene in self.scene_manager.loaded_scenes.values():
            for npc in getattr(scene, "npcs", []):
                if hasattr(npc, "refresh_locale"):
                    npc.refresh_locale()
            if hasattr(scene, "refresh_locale"):
                scene.refresh_locale()
    
    def _setup_font(self):
        """Setup font with Cyrillic support."""
        from src.core.font_setup import apply_ui_font, load_cyrillic_font

        self.cyrillic_font = load_cyrillic_font()
        apply_ui_font(self.cyrillic_font)
    
    def _setup_window(self):
        """Setup game window"""
        self.disableMouse()
        self.accept("window-event", self._on_window_event)

        cfg = self.game_config["window"]
        width = cfg.get("width", 1920)
        height = cfg.get("height", 1080)
        fullscreen = bool(cfg.get("fullscreen", False))

        try:
            applied_w, applied_h = self._apply_window_properties(width, height, fullscreen)
            if applied_w != width or applied_h != height or fullscreen:
                self._sync_window_config(applied_w, applied_h, fullscreen)
            logger.info(
                "Window initialized: %sx%s fullscreen=%s (native=%sx%s)",
                applied_w, applied_h, fullscreen,
                *self._get_native_display_size(),
            )
        except Exception as e:
            logger.warning("Failed to apply initial window properties: %s", e)

        self._schedule_camera_aspect_update()

        self.cam.setPos(0, -120, 0)
        self.cam.lookAt(0, 0, 0)
    
    def _delayed_camera_setup(self, task):
        """Setup camera after window is ready"""
        self._update_camera_aspect_ratio()
        return task.done
    
    def _update_camera_aspect_ratio(self):
        """Update camera lens to match current window aspect ratio"""
        window_width, window_height = self._get_window_pixel_size()
        aspect_ratio = window_width / window_height if window_height > 0 else 16 / 9

        if not hasattr(self, "_ortho_lens") or self._ortho_lens is None:
            self._ortho_lens = OrthographicLens()

        view_width = 70.0
        view_height = view_width / aspect_ratio
        self._ortho_lens.setFilmSize(view_width, view_height)
        self._ortho_lens.setNearFar(-1000, 1000)

        cam_node = self.cam.node()
        if cam_node:
            cam_node.setLens(self._ortho_lens)
        else:
            logger.warning("Could not access camera node, using default lens")

        logger.info(
            "Camera lens updated: aspect=%.2f, view=%.1fx%.1f, window=%sx%s",
            aspect_ratio, view_width, view_height, window_width, window_height,
        )
    
    
    def _setup_scenes(self):
        """Setup all game scenes (lazy loading)"""
        # Main menu is loaded immediately (used on startup)
        main_menu = MainMenuScene(self)
        main_menu.on_play = self.start_game
        main_menu.on_quit = self.quit_game
        self.scene_manager.add_scene("main_menu", main_menu)
        
        # Register factory functions for lazy loading game scenes
        # These will be created only when player enters them
        self.scene_manager.register_scene_factory("cave", lambda base, *args, **kwargs: CaveScene(base))
        self.scene_manager.register_scene_factory("kitchen", lambda base, *args, **kwargs: KitchenScene(base))
        # Minigame needs balance config
        self.scene_manager.register_scene_factory("minigame", lambda base, *args, **kwargs: MinigameScene(base, self.balance))
        
        logger.info("✅ Scenes setup complete (lazy loading enabled)")
    
    def _check_brainlink_startup(self, task):
        """Check BrainLink status on startup"""
        menu = self.scene_manager.loaded_scenes.get("main_menu")
        if not menu:
            return task.done
        
        # Check if Shared Memory is already available
        if self.brainlink_launcher.is_shared_memory_running():
            menu.update_brainlink_status(
                t("brainlink_status.connected"),
                t("brainlink_status.ready"),
                (0.2, 1.0, 0.2, 1)
            )
            menu.enable_play_button()
            logger.info("✅ BrainLink Shared Memory already running")
            return task.done
        
        # Check if BrainLinkClient process is running (but Shared Memory not enabled)
        is_process_running = self.brainlink_launcher.is_process_running()
        
        if is_process_running:
            # Process is running, but Shared Memory is not enabled
            logger.info("⚠️ BrainLinkClient is running, but Shared Memory is not enabled")
            menu.update_brainlink_status(
                t("brainlink_status.restarting"),
                t("brainlink_status.enabling_shared_memory"),
                (1, 1, 0, 1)
            )
            
            # Try to restart with Shared Memory
            if self.brainlink_launcher.restart_with_shared_memory():
                # Wait for Shared Memory to become available
                menu.update_brainlink_status(
                    t("brainlink_status.connecting"),
                    t("brainlink_status.waiting_shared_memory"),
                    (1, 1, 0, 1)
                )
                self.taskMgr.doMethodLater(3.0, self._verify_connection, "verify_connection")
            else:
                menu.update_brainlink_status(
                    t("brainlink_status.restart_failed"),
                    t("brainlink_status.restart_failed_info"),
                    (1, 0.5, 0, 1)
                )
                menu.enable_play_button()  # Allow playing without BrainLink
            return task.done
        
        # BrainLinkClient not running, try to find and launch
        menu.update_brainlink_status(
            t("brainlink_status.searching"),
            t("brainlink_status.looking_for_client"),
            (1, 1, 0, 1)
        )
        
        # If path is already saved, use it; otherwise search
        path = None
        if self.brainlink_launcher.brainlink_path:
            # Verify saved path still exists
            main_py = self.brainlink_launcher.brainlink_path / "main.py"
            if main_py.exists():
                path = self.brainlink_launcher.brainlink_path
                logger.info(f"Using saved BrainLink path: {path}")
        
        if not path:
            path = self.brainlink_launcher.find_brainlink_client()
        
        if path:
            # Found! Try to launch
            menu.update_brainlink_status(
                t("brainlink_status.launching"),
                t("brainlink_status.starting_client"),
                (1, 1, 0, 1)
            )
            
            if self.brainlink_launcher.launch():
                # Wait for connection
                menu.update_brainlink_status(
                    t("brainlink_status.connecting"),
                    t("brainlink_status.waiting_shared_memory"),
                    (1, 1, 0, 1)
                )
                
                # Check connection in background
                self.taskMgr.doMethodLater(3.0, self._verify_connection, "verify_connection")
            else:
                menu.update_brainlink_status(
                    t("brainlink_status.launch_failed"),
                    t("brainlink_status.could_not_start"),
                    (1, 0.2, 0.2, 1)
                )
                menu.enable_play_button()  # Allow playing without BrainLink
        else:
            # Not found
            menu.update_brainlink_status(
                t("brainlink_status.not_found"),
                t("brainlink_status.not_found_info"),
                (1, 0.5, 0, 1)
            )
            menu.enable_play_button()  # Allow playing without BrainLink
        
        return task.done
    
    def _verify_connection(self, task):
        """Verify BrainLink connection"""
        menu = self.scene_manager.loaded_scenes.get("main_menu")
        if not menu:
            return task.done
        
        if self.brainlink_launcher.wait_for_connection(timeout=8.0):
            menu.update_brainlink_status(
                t("brainlink_status.connected"),
                t("brainlink_status.ready_mind"),
                (0.2, 1.0, 0.2, 1)
            )
            menu.enable_play_button()
            logger.info("✅ BrainLink connected successfully")
        else:
            menu.update_brainlink_status(
                t("brainlink_status.started_not_connected"),
                t("brainlink_status.started_not_connected_info"),
                (1, 0.5, 0, 1)
            )
            menu.enable_play_button()
            logger.warning("BrainLink connection timeout")
        
        return task.done
    
    def start_game(self):
        """Start the game (from menu)"""
        logger.info("🎮 Starting game!")
        
        # First hide main menu
        current_scene = self.scene_manager.get_current_scene()
        if current_scene and hasattr(current_scene, 'exit'):
            current_scene.exit()
        
        # Show HUD and enter game mode
        self.in_game = True
        self.hud.show()
        
        # Switch to cave
        self.scene_manager.switch_to("cave", self.player)
        
        # Reset player state
        self.health_system.current_hp = self.health_system.max_hp
        self.energy_system.current_energy = self.energy_system.max_energy
        
        # Enable continuous render forcing for first few frames (fixes gray screen)
        self._just_started_game = True
        self._start_frame_count = 0
        
        # Force immediate render update with multiple passes
        try:
            # Ensure window is ready
            if hasattr(self, 'win') and self.win:
                for _ in range(20):
                    self.graphicsEngine.renderFrame()
                    self.graphicsEngine.syncFrame()
                # Also trigger a window update to force refresh
                try:
                    self.win.requestProperties(self.win.getProperties())
                except:
                    pass
            logger.debug("Forced immediate render update after game start")
        except Exception as e:
            logger.warning(f"Error in immediate render update: {e}")
    
    def quit_game(self):
        """Quit game"""
        logger.info("👋 Quitting game...")
        self.userExit()
    
    def on_action_pressed(self):
        """Handle action button press (Space) - only for NPC interactions"""
        # If dialog is open, continue it
        if self.dialog_box.is_visible:
            self.dialog_box.on_continue()
            return
        
        # Check for NPC interaction only (exits are automatic)
        if not self.in_game:
            return
            
        current_scene = self.scene_manager.get_current_scene()
        if current_scene:
            player_pos = self.player.get_position()
            
            # First check if player is at exit - exits have priority over NPC interactions
            exit_info = current_scene.check_exits(player_pos)
            if exit_info and exit_info.get("target_scene") == "minigame":
                # If at minigame exit, don't allow direct NPC interaction
                # The exit dialog will be handled in update() loop
                logger.debug("Player at minigame exit, skipping direct NPC interaction")
                return
            
            # Check for NPC interaction
            # But only if player is NOT at exit (to prevent showing regular dialog when at exit)
            exit_info = current_scene.check_exits(player_pos)
            if not exit_info:  # Only allow NPC interaction if not at any exit
                npc = current_scene.get_nearby_npc(player_pos)
                if npc:
                    dialog = npc.get_current_dialog()
                    if dialog:
                        self.dialog_box.show(npc, dialog)
                        logger.info(f"💬 Talking to {npc.name} (regular dialog)")
            else:
                logger.debug("Player at exit, skipping regular NPC interaction")
    
    def _on_escape(self):
        """Toggle pause menu when ESC is pressed (only in game)."""
        if not self.in_game:
            return
        if self.dialog_box.is_visible:
            return
        if self.pause_menu.is_visible:
            self.pause_menu.hide()
        else:
            self.pause_menu.show()
    
    def _on_sit_pause(self):
        """Sit + pause game (key from Controls: sit_pause)."""
        if not self.in_game:
            return
        if self.dialog_box.is_visible:
            return
        if not self.pause_menu.is_visible:
            self.pause_menu.show()
    
    def _on_pause_restart(self):
        """Restart current stage (minigame)."""
        self.pause_menu.hide()
        scene = self.scene_manager.get_current_scene()
        scene_id = self.scene_manager.get_current_scene_name()
        if scene_id == "minigame" and scene and getattr(scene, "monkey_mode", None):
            self.scene_manager.switch_to("minigame", self.player, scene.monkey_mode)
            self.health_system.current_hp = self.health_system.max_hp
            self.energy_system.current_energy = self.energy_system.max_energy
        else:
            logger.info("Restart only available in minigame")
    
    def _on_pause_load(self):
        """Load game from save."""
        self.pause_menu.hide()
        game_data = self.save_system.load_game()
        if not game_data:
            logger.info("No save file to load")
            return
        self.progression_system.level = game_data.get("level", 1)
        self.progression_system.current_xp = game_data.get("current_xp", 0)
        self.progression_system.upgrade_levels = game_data.get("upgrade_levels", {}).copy()
        self._apply_upgrades()
        self.health_system.current_hp = self.health_system.max_hp
        self.energy_system.current_energy = self.energy_system.max_energy
        scene_id = game_data.get("current_scene", "cave")
        self.scene_manager.switch_to(scene_id, self.player)
        logger.info(f"Game loaded, scene: {scene_id}")
    
    def _on_pause_settings(self):
        """Open settings (main menu with settings panel). Scene kept in memory so returning does not reset game."""
        self.pause_menu.hide()
        self.in_game = False
        self.hud.hide()
        return_scene_id = self.scene_manager.get_current_scene_name()
        self._return_scene_id = return_scene_id
        self._from_pause_settings = True
        self.scene_manager.switch_to("main_menu", self.player, keep_previous=True)
        menu = self.scene_manager.get_current_scene()
        if menu and hasattr(menu, "_on_settings_clicked"):
            menu._on_settings_clicked()
        if menu and hasattr(menu, "_update_from_pause_buttons"):
            menu._update_from_pause_buttons()

    def _return_from_settings_to_game(self):
        """Return to game from settings (without resetting)."""
        if not getattr(self, "_return_scene_id", None):
            return
        self._from_pause_settings = False
        scene_id = self._return_scene_id
        self._return_scene_id = None
        self.in_game = True
        self.hud.show()
        self.scene_manager.switch_to(scene_id, self.player)
        logger.info("Returned to game from settings: %s", scene_id)
    
    def _on_pause_exit(self):
        """Exit to main menu / quit game."""
        self.pause_menu.hide()
        self.in_game = False
        self.hud.hide()
        self.scene_manager.switch_to("main_menu", self.player)
    
    def update(self, task):
        """Main game update loop"""
        dt = globalClock.getDt()
        
        # Force render for first few frames after game start (fixes gray screen)
        if self._just_started_game:
            self._start_frame_count += 1
            if self._start_frame_count <= 30:  # Force render for 30 frames
                try:
                    # Multiple render passes per frame
                    for _ in range(2):
                        self.graphicsEngine.renderFrame()
                        self.graphicsEngine.syncFrame()
                except:
                    pass
            elif self._start_frame_count > 30:
                self._just_started_game = False
                self._start_frame_count = 0
        
        # Update input
        self.input_manager.update(dt)
        
        # При диалоге или паузе — сбросить весь ввод, чтобы движение не «залипало»
        if self.dialog_box.is_visible or self.pause_menu.is_visible:
            if not getattr(self, "_input_cleared_for_modal", False):
                self._input_cleared_for_modal = True
                self.input_manager.clear_state()
        else:
            self._input_cleared_for_modal = False
        
        # Sitting: hold Space = sit, 2x energy regen, send "stop" to BrainLink
        sitting = self.in_game and not self.dialog_box.is_visible and self.input_manager.is_action_pressed()
        self.player.is_sitting = sitting
        # Visual: squat when sitting
        if sitting:
            self.player.node.setScale(1, 1, 0.75)
        else:
            self.player.node.setScale(1, 1, 1)
        regen_mult = 2.0 if sitting else 1.0
        self.energy_system.update(dt, regen_multiplier=regen_mult)
        
        # While sitting (Space held), send "stop" to BrainLink — one command per throttle (Type 2 = ML+history, else Type 1 = history)
        if sitting and self.input_manager.brainlink and self.input_manager.brainlink.is_connected():
            send_events = getattr(self.input_manager, 'send_brainlink_events', True) or getattr(self.input_manager, 'send_to_history', True) or getattr(self.input_manager, 'send_to_ml', False)
            if send_events:
                import time
                now = time.time()
                if not hasattr(self, '_last_stop_sent_time'):
                    self._last_stop_sent_time = 0.0
                if now - self._last_stop_sent_time >= 0.5:
                    if getattr(self.input_manager, 'send_to_ml', False):
                        if self.input_manager.brainlink.send_event_for_ml_training("stop"):
                            self._last_stop_sent_time = now
                    elif getattr(self.input_manager, 'send_to_history', True):
                        if self.input_manager.brainlink.send_event_to_history("stop"):
                            self._last_stop_sent_time = now
        
        # When pause menu is open: freeze game, don't update scene or movement
        if self.pause_menu.is_visible:
            if self.in_game:
                self.hud.update_hp(self.health_system.current_hp, self.health_system.max_hp)
                self.hud.update_energy(self.energy_system.get_percentage())
                self.hud.update_level(self.progression_system.level)
                pred, conn, conf, probs = self.input_manager.get_ml_display_info()
                self.hud.update_ml_display(pred, conn, conf, probs)
            return task.cont
        
        # Update scene
        self.scene_manager.update(dt)
        
        # Process movement (only if in game and not in dialog)
        if self.in_game and not self.dialog_box.is_visible:
            # When sitting (Space held), no movement
            move_dir = (0, 0) if sitting else self.input_manager.get_movement()
            
            # Debug logging for BrainLink movement
            if not hasattr(self, '_movement_debug_counter'):
                self._movement_debug_counter = 0
            self._movement_debug_counter += 1
            
            movement_source = self.input_manager.get_movement_source()
            is_brainlink = movement_source == MOVEMENT_SOURCE_BRAINLINK
            # BrainLink speed scale by confidence: below min = no move, min..full = limited speed, >= full = max speed
            brainlink_speed_mult = 1.0
            if is_brainlink and move_dir != (0, 0):
                _, _, conf, _ = self.input_manager.get_ml_display_info()
                bl_cfg = self.game_config.get("brainlink", {})
                min_c = bl_cfg.get("min_confidence", 0.25)
                full_c = bl_cfg.get("full_confidence", 0.7)
                if conf < min_c:
                    move_dir = (0, 0)
                    brainlink_speed_mult = 0.0
                elif conf >= full_c:
                    brainlink_speed_mult = 1.0
                else:
                    brainlink_speed_mult = (conf - min_c) / (full_c - min_c) if full_c > min_c else 1.0
                if move_dir != (0, 0) and self._movement_debug_counter % 60 == 0:
                    logger.info(f"🎮 Game: [BrainLink] movement - dir=({move_dir[0]:.2f}, {move_dir[1]:.2f}), conf={conf:.2f}, speed_mult={brainlink_speed_mult:.2f}")
            
            if move_dir != (0, 0):
                # Get current scene for movement restrictions
                current_scene = self.scene_manager.get_current_scene()
                
                # Only spend energy when movement is from keyboard (not BrainLink)
                should_spend_energy = movement_source == MOVEMENT_SOURCE_KEYBOARD
                if self._movement_debug_counter % 60 == 0 and movement_source == MOVEMENT_SOURCE_KEYBOARD:
                    logger.info(f"🎮 Game: [Keyboard] movement - dir=({move_dir[0]:.2f}, {move_dir[1]:.2f})")
                
                if should_spend_energy:
                    # Try to spend energy (only for keyboard movement)
                    if self.energy_system.spend(self.move_cost * dt):
                        bounds = None
                        if current_scene and hasattr(current_scene, 'MOVEMENT_BOUNDS'):
                            bounds = current_scene.MOVEMENT_BOUNDS
                        self.player.move(move_dir[0], move_dir[1], dt, self.player_speed, bounds, current_scene)
                else:
                    # BrainLink movement: speed scaled by confidence (min_confidence..full_confidence)
                    effective_speed = self.player_speed * brainlink_speed_mult
                    bounds = None
                    if current_scene and hasattr(current_scene, 'MOVEMENT_BOUNDS'):
                        bounds = current_scene.MOVEMENT_BOUNDS
                    if self._movement_debug_counter % 60 == 0:
                        logger.info(f"🎮 Game: [BrainLink] movement - speed={effective_speed:.2f} (mult={brainlink_speed_mult:.2f})")
                    self.player.move(move_dir[0], move_dir[1], dt, effective_speed, bounds, current_scene)
            
            # Check for automatic scene transitions (exits work automatically)
            # Only check if dialog is not visible (to prevent spam)
            if not self.dialog_box.is_visible and not self._exit_dialog_shown:
                current_scene = self.scene_manager.get_current_scene()
                if current_scene:
                    player_pos = self.player.get_position()
                    exit_info = current_scene.check_exits(player_pos)
                    if exit_info:
                        target_scene = exit_info.get("target_scene")
                        if target_scene:
                            logger.info(f"🚪 Player entered exit: {exit_info.get('name', 'unknown')}, transitioning to {target_scene}")
                            
                            # Special handling for minigame exit: father intercepts!
                            if target_scene == "minigame":
                                # Father always intercepts when trying to exit cave
                                father = None
                                for npc_obj in current_scene.npcs:
                                    if npc_obj.name == "Father":
                                        father = npc_obj
                                        break
                                
                                if father:
                                    # Only show dialog if it's not already shown
                                    if not self._exit_dialog_shown:
                                        # Use father's exit_dialog, but update callback
                                        exit_dialog = resolve_dialog(father.exit_dialog)
                                        exit_dialog["options"] = [
                                            (t("npc.father.play_minigame"), self._on_father_agrees_to_minigame)
                                        ]
                                        self.dialog_box.show(father, exit_dialog)
                                        self._exit_dialog_shown = True  # Mark that dialog was shown
                                        logger.info("Father intercepted exit attempt! Showing exit dialog with Play Minigame option")
                                    else:
                                        logger.debug("Father exit dialog already shown, skipping")
                                else:
                                    # Fallback: show position dialog directly
                                    logger.warning("Father not found, showing position dialog directly")
                                    self._show_minigame_position_dialog()
                                    self._exit_dialog_shown = True
                            else:
                                # Normal scene transition
                                self.scene_manager.switch_to(target_scene, self.player)
                                logger.info(f"✅ Transitioned to {target_scene}")
            else:
                # Reset exit dialog flag if player moved away from exit
                if self._exit_dialog_shown:
                    current_scene = self.scene_manager.get_current_scene()
                    if current_scene:
                        player_pos = self.player.get_position()
                        exit_info = current_scene.check_exits(player_pos)
                        if not exit_info:  # Player moved away from exit
                            self._exit_dialog_shown = False
        
        # Update HUD (only in game)
        if self.in_game:
            self.hud.update_hp(self.health_system.current_hp, self.health_system.max_hp)
            self.hud.update_energy(self.energy_system.get_percentage())
            self.hud.update_level(self.progression_system.level)
            pred, conn, conf, probs = self.input_manager.get_ml_display_info()
            self.hud.update_ml_display(pred, conn, conf, probs)
        
        return task.cont
    
    def _on_level_up(self, new_level: int):
        """Handle level up event"""
        logger.info(f"🎉 Level up! New level: {new_level}")
        # Could add visual effects here
    
    def _apply_upgrades(self):
        """Apply upgrade values to game systems"""
        # Apply HP upgrade
        hp_bonus = int(self.progression_system.get_upgrade_value("max_hp"))
        if hp_bonus > 0:
            self.health_system.max_hp = self.game_config["player"]["initial_hp"] + hp_bonus
            self.health_system.current_hp = min(self.health_system.current_hp, self.health_system.max_hp)
        
        # Apply energy upgrade
        energy_bonus = self.progression_system.get_upgrade_value("max_energy")
        if energy_bonus > 0:
            self.energy_system.max_energy = self.game_config["player"]["initial_energy"] + energy_bonus
            self.energy_system.current_energy = min(self.energy_system.current_energy, self.energy_system.max_energy)
        
        # Apply energy regen upgrade
        regen_bonus = self.progression_system.get_upgrade_value("energy_regen")
        if regen_bonus > 0:
            self.energy_system.regen_rate = self.game_config["player"]["energy_regen_rate"] + regen_bonus
        
        # Apply move speed upgrade
        speed_bonus = self.progression_system.get_upgrade_value("move_speed")
        if speed_bonus > 0:
            self.player_speed = self.game_config["player"]["move_speed"] + speed_bonus
    
    def _on_father_agrees_to_minigame(self):
        """Called when father agrees to play minigame"""
        logger.info("Father agreed to play minigame - showing position dialog")
        # Keep flag True to prevent father dialog from showing again
        # It will be reset when player exits the area or starts minigame
        self.dialog_box.hide()
        # Small delay to ensure dialog is fully closed before showing new one
        self.taskMgr.doMethodLater(0.15, self._show_minigame_position_dialog_delayed, "show_position_dialog")
    
    def _show_minigame_position_dialog_delayed(self, task):
        """Show position dialog with delay"""
        self._show_minigame_position_dialog()
        return task.done
    
    def _show_minigame_position_dialog(self):
        """Show dialog to select starting position for minigame; show leader name and time (non-cheater) per mode."""
        if self.dialog_box.is_visible:
            self.dialog_box.hide()
        
        class SystemNPC:
            name = t("minigame.system")
        system_npc = SystemNPC()
        
        leader_text = ""
        if hasattr(self, 'save_system') and self.save_system:
            ns_name, ns_time = self.save_system.get_leader("NorthSouth")
            we_name, we_time = self.save_system.get_leader("WestEast")
            leader_text = (
                f"\n\n{t('minigame.leader_ns', name=ns_name, time=ns_time)}"
                f"\n{t('minigame.leader_we', name=we_name, time=we_time)}"
            )
        
        dialog = {
            "title_key": "minigame.mode_title",
            "text": t("minigame.mode_text") + leader_text,
            "options": [
                (t("minigame.mode_ns"), lambda: self._start_minigame_with_position("NorthSouth")),
                (t("minigame.mode_we"), lambda: self._start_minigame_with_position("WestEast")),
            ],
        }
        
        logger.info("Showing minigame mode selection dialog with leaders")
        self.dialog_box.show(system_npc, dialog)
    
    def _start_minigame_with_position(self, monkey_mode: str):
        """Start minigame with selected mode
        
        Args:
            monkey_mode: "NorthSouth" or "WestEast" - determines where monkeys walk
        """
        logger.info(f"Starting minigame with mode: {monkey_mode}")
        self._exit_dialog_shown = False  # Reset flag when starting minigame
        self.dialog_box.hide()
        # Store mode for scene manager
        self._pending_minigame_position = monkey_mode
        # Use scene manager to switch (it will handle lazy loading)
        self.scene_manager.switch_to("minigame", self.player, monkey_mode)
    
    def cleanup(self):
        """Cleanup on exit"""
        logger.info("🛑 Shutting down...")
        
        self.input_manager.cleanup()
        self.scene_manager.cleanup()
        self.player.cleanup()
        self.hud.cleanup()
        self.dialog_box.cleanup()
        self.brainlink_launcher.cleanup()
