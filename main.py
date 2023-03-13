import logging
import os

import src.scraper.main as scraper

logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] %(message)s",
    level=logging.INFO if not os.environ.get("DEBUG", False) else logging.DEBUG,
)


if __name__ == "__main__":
    scraper.main()
