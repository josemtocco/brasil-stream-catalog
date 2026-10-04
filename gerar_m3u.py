import logging
from pathlib import Path
from src.core import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    result = run(root)
    logging.info("Resultado: %s", result)
