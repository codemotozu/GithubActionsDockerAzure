# server/app/main.py
import uvicorn
from app.infrastructure.api.routes import app
import os
import logging
from datetime import datetime

# Configure logging first to capture all events
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ],
    force=True  # Override any existing log configurations
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Log initialization details
    logger.info("🔧 Initializing SpeakAndTranslate Azure Server")
    logger.debug(f"Python version: {os.sys.version}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    logger.debug(f"Environment variables: {dict(os.environ)}")

    # Create audio directory with proper permissions
    audio_dir = "/tmp/tts_audio" if os.name != "nt" else os.path.join(
        os.environ.get("TEMP", ""), "tts_audio"
    )
    
    try:
        os.makedirs(audio_dir, exist_ok=True)
        os.chmod(audio_dir, 0o755)
        logger.info(f"✅ Created audio directory at {audio_dir}")
        
        # Verify write permissions
        test_file = os.path.join(audio_dir, "permission_test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        logger.debug("✅ Verified audio directory write permissions")
        
    except Exception as e:
        logger.critical(f"❌ Failed to create audio directory: {str(e)}")
        raise

    # Configure server parameters
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"  # Always bind to all interfaces in container
    # host = "127.0.0.1", # here you can hear the translaion in my local machine dont forget to update impl.dart
   
    # Log final configuration
    logger.info("⚙️ Final Configuration:")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Azure Speech Key: {'set' if os.getenv('AZURE_SPEECH_KEY') else 'missing'}")
    logger.info(f"Azure Region: {os.getenv('AZURE_SPEECH_REGION', 'not configured')}")
    logger.info(f"TTS Device: {os.getenv('TTS_DEVICE', 'cpu')}")
    logger.info(f"Container Env: {os.getenv('CONTAINER_ENV', 'false')}")

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
    
    
