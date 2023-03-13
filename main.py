import logging
import os
import sys

import src.scraper.main as scraper

logging.basicConfig(
    stream=sys.stdout,
    format="[%(asctime)s - %(levelname)s] %(message)s",
    level=logging.INFO if not os.environ.get("DEBUG", False) else logging.DEBUG,
)


if __name__ == "__main__":
    scraper.main()
