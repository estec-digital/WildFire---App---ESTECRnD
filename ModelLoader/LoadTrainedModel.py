import torch
from UserInput.InputModel import iModel
import logging, os, sys

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

# ModelLoader
def loadModel(input_json_path):
    try:
        # Detect if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device.upper()}")

        modelFolder = iModel(input_json_path)
        model = torch.hub.load((r"{}".format(modelFolder)), 'custom',
                               path=r"{}/best.pt".format(modelFolder), source='local')
        
        model.to(device)

        #print("Completed load ML model!", flush=True)
        logger.info(f"Completed load ML model! Using:{device} ")
        return model
    except Exception as e:
        #print(e)
        logger.error(f"\n ModelLoader.LoadTrainedMOdel.loadModel \n  {e}\n")
        #print("Failed to load ML model")
