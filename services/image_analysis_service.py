"""
Computer Vision service for classroom layout analysis (Phase 6).

Approach:
- Lightweight OpenCV pipeline (no heavy neural network required for the first version)
- Works better on floor-plans and clear top-down photos than on cluttered perspective photos
- Detects rectangular-like regions that may correspond to desks/seats
- Returns candidate seat positions for administrator review
- Administrator confirmation is mandatory
"""
from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import uuid
import cv2
import numpy as np
from PIL import Image

from config import CLASSROOM_IMAGES_DIR


@dataclass
class Detection:
    """A single detected seat/desk candidate."""
    x: int                  # top-left x in image pixels
    y: int                  # top-left y
    width: int
    height: int
    center_x: int
    center_y: int
    confidence: float       # simple heuristic score 0-1
    label: str = "seat"


@dataclass
class AnalysisResult:
    """Result of running the image analyzer."""
    success: bool
    message: str
    image_path: Optional[str] = None
    annotated_path: Optional[str] = None
    detections: List[Detection] = None
    image_width: int = 0
    image_height: int = 0
    method: str = "opencv_contours"

    def __post_init__(self):
        if self.detections is None:
            self.detections = []


def save_uploaded_image(uploaded_file, prefix: str = "classroom") -> Path:
    """Save an uploaded file to the classroom_images directory and return the path."""
    CLASSROOM_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(uploaded_file.name).suffix.lower() or ".jpg"
    filename = f"{prefix}_{uuid.uuid4().hex[:10]}{ext}"
    path = CLASSROOM_IMAGES_DIR / filename
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


def _load_image(path: Path) -> Optional[np.ndarray]:
    img = cv2.imread(str(path))
    if img is None:
        # fallback via PIL
        try:
            pil = Image.open(path).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        except Exception:
            return None
    return img


def analyze_classroom_image(
    image_path: Path,
    min_area_ratio: float = 0.0015,
    max_area_ratio: float = 0.08,
    min_aspect: float = 0.4,
    max_aspect: float = 2.5,
) -> AnalysisResult:
    """
    Lightweight contour-based detector.

    Strategy:
    1. Convert to grayscale + blur
    2. Adaptive threshold / Canny edges
    3. Find contours
    4. Filter by area and aspect ratio (desk-like rectangles)
    5. Return bounding boxes as candidate seats
    """
    img = _load_image(image_path)
    if img is None:
        return AnalysisResult(False, "Could not read the image file.")

    h, w = img.shape[:2]
    if h < 50 or w < 50:
        return AnalysisResult(False, "Image is too small.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection
    edges = cv2.Canny(blurred, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = min_area_ratio * (w * h)
    max_area = max_area_ratio * (w * h)

    detections: List[Detection] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue

        x, y, bw, bh = cv2.boundingRect(cnt)
        if bh == 0:
            continue
        aspect = bw / float(bh)
        if aspect < min_aspect or aspect > max_aspect:
            continue

        # Simple confidence: prefer medium-sized, roughly rectangular shapes
        rect_area = bw * bh
        extent = area / rect_area if rect_area > 0 else 0
        conf = min(1.0, max(0.2, extent * 0.9))

        detections.append(Detection(
            x=int(x), y=int(y),
            width=int(bw), height=int(bh),
            center_x=int(x + bw / 2),
            center_y=int(y + bh / 2),
            confidence=round(conf, 2),
        ))

    # Sort top-to-bottom, left-to-right
    detections.sort(key=lambda d: (d.center_y // 40, d.center_x))

    # Draw annotations
    annotated = img.copy()
    for i, d in enumerate(detections, 1):
        color = (0, 200, 0) if d.confidence >= 0.5 else (0, 165, 255)
        cv2.rectangle(annotated, (d.x, d.y), (d.x + d.width, d.y + d.height), color, 2)
        cv2.putText(
            annotated, f"{i}", (d.x + 3, d.y + 16),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA
        )

    # Save annotated image
    ann_name = f"annotated_{image_path.stem}.jpg"
    ann_path = CLASSROOM_IMAGES_DIR / ann_name
    cv2.imwrite(str(ann_path), annotated)

    msg = (
        f"Detected {len(detections)} candidate seat/desk regions. "
        "These are proposals only — please review and correct before confirming."
    )
    return AnalysisResult(
        success=True,
        message=msg,
        image_path=str(image_path),
        annotated_path=str(ann_path),
        detections=detections,
        image_width=w,
        image_height=h,
        method="opencv_contours",
    )


def detections_to_grid_proposal(
    detections: List[Detection],
    image_width: int,
    image_height: int,
    target_rows: Optional[int] = None,
    target_cols: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Attempt to organize detections into an approximate row/column grid.
    Returns a simple proposal the administrator can accept or override.
    """
    if not detections:
        return {"rows": 0, "columns": 0, "seats": []}

    # Cluster by y-coordinate to estimate rows
    ys = sorted(d.center_y for d in detections)
    row_threshold = max(30, image_height // 25)

    rows_list = []
    current = [ys[0]]
    for y in ys[1:]:
        if y - current[-1] < row_threshold:
            current.append(y)
        else:
            rows_list.append(current)
            current = [y]
    rows_list.append(current)

    estimated_rows = len(rows_list)
    # Estimate columns from the densest row
    estimated_cols = max(len(r) for r in rows_list) if rows_list else 0

    if target_rows:
        estimated_rows = target_rows
    if target_cols:
        estimated_cols = target_cols

    return {
        "estimated_rows": estimated_rows,
        "estimated_columns": estimated_cols,
        "num_detections": len(detections),
        "note": "Grid estimate is approximate. Prefer manual confirmation of rows/columns.",
    }
