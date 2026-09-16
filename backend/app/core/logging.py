import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,  # change to DEBUG for everything
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True,  # overwrite any existing config
    )