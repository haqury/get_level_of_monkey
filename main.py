#!/usr/bin/env python
"""
Fucking Pickup - Main Entry Point

2D Action game with BrainLink integration!
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
import io

# Custom StreamHandler that handles UTF-8 encoding properly on Windows
class UTF8StreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        if stream is None:
            stream = sys.stdout
        super().__init__(stream)
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Try to encode to UTF-8, replace invalid characters if needed
            if hasattr(stream, 'buffer'):
                stream.buffer.write(msg.encode('utf-8', errors='replace'))
                stream.buffer.write(self.terminator.encode('utf-8'))
                stream.buffer.flush()
            else:
                stream.write(msg + self.terminator)
                stream.flush()
        except Exception:
            self.handleError(record)

# Setup handlers
stream_handler = UTF8StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# File handler with UTF-8 encoding
file_handler = logging.FileHandler('game.log', mode='w', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[stream_handler, file_handler]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fucking Pickup - 2D Action Game")
    parser.add_argument("--auto-start", action="store_true", 
                       help="Automatically start game after menu loads (for testing)")
    parser.add_argument("--auto-start-delay", type=float, default=3.0,
                       help="Delay in seconds before auto-starting game")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🎮 Fucking Pickup")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Controls:")
    logger.info("  🎮 Keyboard: Arrow keys + Space")
    logger.info("  🧠 BrainLink: Think ml/mr/mu/md!")
    logger.info("")
    logger.info("Make sure BrainLink Client is running with Shared Memory enabled!")
    logger.info("")
    logger.info("=" * 60)
    
    try:
        from src.core.game import Game
        
        game = Game()
        
        # Auto-start game if requested
        if args.auto_start:
            logger.info(f"Auto-start enabled: will start game after {args.auto_start_delay}s")
            def auto_start_task(task):
                if game.scene_manager.get_current_scene_name() == "main_menu":
                    menu = game.scene_manager.scenes.get("main_menu")
                    if menu and menu.play_btn['state'] != 'disabled':
                        logger.info("Auto-starting game...")
                        game.start_game()
                        return task.done
                return task.cont
            game.taskMgr.doMethodLater(args.auto_start_delay, auto_start_task, "auto_start_game")
        
        game.run()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Game interrupted by user")
    
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        return 1
    
    finally:
        logger.info("👋 Thanks for playing!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
