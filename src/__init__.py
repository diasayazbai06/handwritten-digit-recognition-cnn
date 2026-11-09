"""DigitNet: қолжазба цифрларды CNN арқылы тану жобасының бастапқы коды."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
EXPERIMENTS = OUTPUTS / "experiments"
MODELS = ROOT / "models"
CONFIGS = ROOT / "configs"

for _d in (OUTPUTS, FIGURES, EXPERIMENTS, MODELS):
    _d.mkdir(parents=True, exist_ok=True)
