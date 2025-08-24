# server/app/main.py
import uvicorn
from app.infrastructure.api.routes import app
import os
import logging
from datetime import datetime
import sys
import io

# Configure logging with UTF-8 encoding support
class UTF8StreamHandler(logging.StreamHandler):
    """A StreamHandler that properly handles UTF-8 encoding"""
    def __init__(self):
        # Force UTF-8 encoding for stdout on Windows
        if sys.platform == 'win32':
            # Reconfigure stdout to use UTF-8
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        super().__init__()
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Ensure we can handle Unicode
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # Fallback: replace emojis with text equivalents
            msg = msg.encode('ascii', 'replace').decode('ascii')
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Configure logging first to capture all events
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        UTF8StreamHandler(),  # Use our custom UTF-8 handler
        logging.FileHandler("api.log", encoding='utf-8')  # Ensure file handler uses UTF-8
    ],
    force=True  # Override any existing log configurations
)
logger = logging.getLogger(__name__)

# Alternative: Define emoji-free messages for Windows compatibility
def get_log_message(emoji_version, text_version):
    """Return emoji version on non-Windows systems, text version on Windows"""
    if sys.platform == 'win32' and sys.stdout.encoding != 'utf-8':
        return text_version
    return emoji_version

if __name__ == "__main__":
    # Log initialization details
    logger.info(get_log_message("🔧 Initializing SpeakAndTranslate Azure Server", 
                                "[INIT] Initializing SpeakAndTranslate Azure Server"))
    logger.debug(f"Python version: {os.sys.version}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    logger.debug(f"Environment variables: {dict(os.environ)}")

    # Create audio directory with proper permissions
    audio_dir = "/tmp/tts_audio" if os.name != "nt" else os.path.join(
        os.environ.get("TEMP", ""), "tts_audio"
    )
    
    try:
        os.makedirs(audio_dir, exist_ok=True)
        # Only set chmod on Unix-like systems
        if os.name != "nt":
            os.chmod(audio_dir, 0o755)
        logger.info(get_log_message(f"✅ Created audio directory at {audio_dir}", 
                                   f"[OK] Created audio directory at {audio_dir}"))
        
        # Verify write permissions
        test_file = os.path.join(audio_dir, "permission_test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        logger.debug(get_log_message("✅ Verified audio directory write permissions", 
                                    "[OK] Verified audio directory write permissions"))
        
    except Exception as e:
        logger.critical(get_log_message(f"❌ Failed to create audio directory: {str(e)}", 
                                       f"[ERROR] Failed to create audio directory: {str(e)}"))
        raise

    # Configure server parameters
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"  # Always bind to all interfaces in container
    # host = "127.0.0.1", # here you can hear the translaion in my local machine dont forget to update impl.dart
   
    # Log final configuration
    logger.info(get_log_message("⚙️ Final Configuration:", "[CONFIG] Final Configuration:"))
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Azure Speech Key: {'set' if os.getenv('AZURE_SPEECH_KEY') else 'missing'}")
    logger.info(f"Azure Region: {os.getenv('AZURE_SPEECH_REGION', 'not configured')}")
    logger.info(f"TTS Device: {os.getenv('TTS_DEVICE', 'cpu')}")
    logger.info(f"Container Env: {os.getenv('CONTAINER_ENV', 'false')}")

    # Initialize high-speed neural translation optimization (simplified to avoid timeout issues)
    logger.info(get_log_message("🧠 Initializing High-Speed Neural Translation System", 
                                "[NEURAL] Initializing High-Speed Neural Translation System"))
    
    try:
        # Import the high-speed optimizer (initialization only, no complex startup)
        from app.application.services.high_speed_optimizer import high_speed_optimizer
        
        # Simple initialization without complex batching to avoid timeout issues
        logger.info(get_log_message("🚀 Neural translation optimizer ready (simplified mode)", 
                                  "[NEURAL] Neural translation optimizer ready (simplified mode)"))
        
    except Exception as e:
        logger.warning(get_log_message(f"⚠️ High-speed optimizer initialization failed: {e}", 
                                     f"[WARN] High-speed optimizer initialization failed: {e}"))
        logger.info("Continuing with standard translation service...")

    # Start the server with detailed UVicorn configuration
    uvicorn.run(
        app,
        host=host,
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_config=None,  # Use our already configured logging
        access_log=False,  # We're handling access logs ourselves
        server_header=False,
        date_header=False,
        timeout_keep_alive=300,
        log_level="debug" if os.getenv("DEBUG_MODE") else "info"
    )