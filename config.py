"""
Global configuration for the Examination Allocation System.
"""
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.resolve()

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
SAMPLE_DIR = DATA_DIR / "sample"
CLASSROOM_IMAGES_DIR = DATA_DIR / "classroom_images"
REPORTS_DIR = DATA_DIR / "generated_reports"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
VISION_MODELS_DIR = ARTIFACTS_DIR / "vision_models"

# Database
DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'exam_allocation.db'}"

# Ensure directories exist
for d in [TEMPLATES_DIR, SAMPLE_DIR, CLASSROOM_IMAGES_DIR, REPORTS_DIR, VISION_MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
