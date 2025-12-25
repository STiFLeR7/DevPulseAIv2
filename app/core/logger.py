import sys
from loguru import logger

# Configure logger to output to stdout
logger.remove()
logger.add(sys.stdout, level="INFO")

# Explicit export
__all__ = ["logger"]
