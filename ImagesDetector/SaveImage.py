from PIL import Image as PImage
import numpy as np
import logging
from datetime import datetime
import sys, os, time

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Setup logging
# === Configure Logging ===
LOG_FILE = "Logs/DATA_AI_ENGINE_service.log"
os.makedirs("Logs", exist_ok=True)  # Ensure log folder exists

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Clear previous handlers
if logger.hasHandlers():
    logger.handlers.clear()

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode='a')
file_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)
# ===========================

def save(results, saveFolder, imageFile):
    try:
        # Ensure target folder exists
        os.makedirs(saveFolder, exist_ok=True)

        # Convert and resize image
        resultImg = PImage.fromarray(np.squeeze(results.render()), 'RGB')
        resizeImg = resultImg.resize((640, 360))

        # Construct path safely
        save_path = os.path.join(saveFolder, imageFile)

        # Save and explicitly flush
        resizeImg.save(save_path)
        resizeImg.close()

        # Ensure file is written to disk
        retry = 5
        while retry > 0:
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                break
            time.sleep(0.1)
            retry -= 1

        if retry == 0:
            logger.warning(f"[SAVE] File exists check failed after retries: {save_path}")
            return None

        #logger.info(f"[SAVE] Result image saved to: {save_path}")
        return save_path

    except Exception as e:
        logger.error(f"[SAVE ERROR] Failed to save result image: {e}")
        return None