import os
import logging

# Get the current directory name
dir_name = os.path.basename(os.getcwd())

# Set up logging
logging.basicConfig(
    filename=f"{dir_name}.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

logger = logging.getLogger(__name__)
