import logging
import os
import sys

hashseed = os.getenv("PYTHONHASHSEED")
if not hashseed or hashseed != "0":
    logging.critical(
        "Hash seed randomization is not disabled. "
        "Please disable it by setting PYTHONHASHSEED=0 environment variable"
    )
    sys.exit(1)

import src.scraper.main as scraper

logging.basicConfig(
    stream=sys.stdout,
    format="[%(asctime)s - %(levelname)s] %(message)s",
    level=logging.INFO if not os.environ.get("DEBUG", False) else logging.DEBUG,
)


if __name__ == "__main__":
    scraper.main()
