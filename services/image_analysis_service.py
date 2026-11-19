
"""
Computer Vision service for classroom layout analysis (Phase 6).

Approach:
- Lightweight OpenCV contour-based detection
- Best suited to simple floor plans and top-down diagrams
- Detects candidate desk/seat regions
- Removes overlapping and nested duplicate detections
- Administrator review and confirmation are mandatory

Note:
This is a heuristic detector, not a trained desk-recognition model.
Real classroom photographs may produce inaccurate results.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import uuid

import cv2
import numpy as np
from PIL import Image

from config import CLASSROOM_IMAGES_DIR


@dataclass
class Detection:
    """A single detected seat/desk candidate."""

    x: int
    y: int
    width: int
    height: int
    center_x: int
    center_y: int
    confidence: float
    label: str = "seat"


@dataclass
class AnalysisResult:
    """Result of running the image analyzer."""

    success: bool
    message: str
    image_path: Optional[str] = None
    annotated_path: Optional[str] = None
    detections: List[Detection] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0
    method: str = "opencv_contours"


def save_uploaded_image(
    uploaded_file,
    prefix: str = "classroom",
) -> Path:
    """Save an uploaded image and return its path."""

    CLASSROOM_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    ext = Path(uploaded_file.name).suffix.lower() or ".jpg"
    filename = f"{prefix}_{uuid.uuid4().hex[:10]}{ext}"

    path = CLASSROOM_IMAGES_DIR / filename

    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return path


def _load_image(path: Path) -> Optional[np.ndarray]:
    """Read an image using OpenCV, with a PIL fallback."""

    img = cv2.imread(str(path))

    if img is None:
        try:
            with Image.open(path) as pil:
                rgb = pil.convert("RGB")
                img = cv2.cvtColor(
                    np.array(rgb),
                    cv2.COLOR_RGB2BGR,
                )
        except Exception:
            return None

    return img


def remove_duplicate_detections(
    detections: List[Detection],
    overlap_threshold: float = 0.75,
) -> List[Detection]:
    """
    Remove overlapping and nested duplicate bounding boxes.

    Overlap is measured against the smaller bounding-box area,
    allowing nested contours to be identified as duplicates.

    Larger bounding boxes are preferred. This is a heuristic:
    it can also merge genuinely separate objects if their boxes
    overlap substantially.
    """

    if not detections:
        return []

    sorted_detections = sorted(
        detections,
        key=lambda d: d.width * d.height,
        reverse=True,
    )

    kept: List[Detection] = []

    for candidate in sorted_detections:
        duplicate = False

        for existing in kept:
            x1 = max(candidate.x, existing.x)
            y1 = max(candidate.y, existing.y)

            x2 = min(
                candidate.x + candidate.width,
                existing.x + existing.width,
            )
            y2 = min(
                candidate.y + candidate.height,
                existing.y + existing.height,
            )

            intersection_width = max(0, x2 - x1)
            intersection_height = max(0, y2 - y1)

            intersection_area = (
                intersection_width * intersection_height
            )

            candidate_area = (
                candidate.width * candidate.height
            )
            existing_area = (
                existing.width * existing.height
            )

            smaller_area = min(
                candidate_area,
                existing_area,
            )

            overlap = (
                intersection_area / smaller_area
                if smaller_area > 0
                else 0.0
            )

            if overlap >= overlap_threshold:
                duplicate = True
                break

        if not duplicate:
            kept.append(candidate)

    return kept


def filter_repeated_desk_groups(
    detections: List[Detection],
    size_tolerance: float = 0.25,
    min_group_size: int = 4,
) -> List[Detection]:
    """
    Keep candidates that share similar dimensions with
    several other candidates.

    Useful for simple floor plans containing repeated desk
    shapes. Not suitable as a universal desk detector.
    """
    if len(detections) < min_group_size:
        return detections

    best_group: List[Detection] = []

    for reference in detections:
        group = []

        for candidate in detections:
            width_difference = (
                abs(candidate.width - reference.width)
                / max(reference.width, 1)
            )
            height_difference = (
                abs(candidate.height - reference.height)
                / max(reference.height, 1)
            )

            if (
                width_difference <= size_tolerance
                and height_difference <= size_tolerance
            ):
                group.append(candidate)

        if len(group) > len(best_group):
            best_group = group

    if len(best_group) >= min_group_size:
        return best_group

    return detections


def analyze_classroom_image(
    image_path: Path,
    min_area_ratio: float = 0.0015,
    max_area_ratio: float = 0.08,
    min_aspect: float = 0.4,
    max_aspect: float = 2.5,
) -> AnalysisResult:
    """
    Detect candidate desk/seat regions using OpenCV.

    Strategy:
    1. Load image
    2. Convert to grayscale and blur
    3. Detect edges
    4. Retrieve internal and external contours
    5. Filter by area and aspect ratio
    6. Remove duplicate bounding boxes
    7. Draw and save annotations
    """

    image_path = Path(image_path)

    img = _load_image(image_path)

    if img is None:
        return AnalysisResult(
            success=False,
            message="Could not read the image file.",
        )

    h, w = img.shape[:2]

    if h < 50 or w < 50:
        return AnalysisResult(
            success=False,
            message="Image is too small.",
            image_width=w,
            image_height=h,
        )

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY,
    )

    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0,
    )

    # Step 1: Detect edges.
    edges = cv2.Canny(
        blurred,
        50,
        150,
    )

    edges = cv2.dilate(
        edges,
        np.ones((3, 3), np.uint8),
        iterations=1,
    )

    # Step 2: Detect all contours, including internal ones.
    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    min_area = min_area_ratio * (w * h)
    max_area = max_area_ratio * (w * h)

    detections: List[Detection] = []

    # Step 3: Convert suitable contours into candidates.
    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area < min_area or area > max_area:
            continue

        x, y, bw, bh = cv2.boundingRect(cnt)

        if bw <= 0 or bh <= 0:
            continue

        aspect = bw / float(bh)

        if aspect < min_aspect or aspect > max_aspect:
            continue

        rect_area = bw * bh

        extent = (
            area / rect_area
            if rect_area > 0
            else 0.0
        )

        # This is a shape-based score, not an AI probability.
        confidence = min(
            1.0,
            max(0.2, extent * 0.9),
        )

        detections.append(
            Detection(
                x=int(x),
                y=int(y),
                width=int(bw),
                height=int(bh),
                center_x=int(x + bw / 2),
                center_y=int(y + bh / 2),
                confidence=round(confidence, 2),
            )
        )

    # Step 4: Remove duplicate and nested candidates.
    detections = remove_duplicate_detections(
        detections,
        overlap_threshold=0.75,
    )
    # Prefer repeated, similarly sized desk groups.
    detections = filter_repeated_desk_groups(
        detections,
        size_tolerance=0.25,
        min_group_size=4,
    )

    # Step 5: Sort approximately from top to bottom,
    # then left to right.
    detections.sort(
        key=lambda d: (
            d.center_y // 40,
            d.center_x,
        )
    )

    # Step 6: Draw the remaining detections.
    annotated = img.copy()

    for i, detection in enumerate(detections, start=1):
        color = (
            (0, 200, 0)
            if detection.confidence >= 0.5
            else (0, 165, 255)
        )

        cv2.rectangle(
            annotated,
            (detection.x, detection.y),
            (
                detection.x + detection.width,
                detection.y + detection.height,
            ),
            color,
            2,
        )

        cv2.putText(
            annotated,
            str(i),
            (
                detection.x + 3,
                detection.y + 16,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )

    # Step 7: Save the annotated preview.
    CLASSROOM_IMAGES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ann_name = f"annotated_{image_path.stem}.jpg"
    ann_path = CLASSROOM_IMAGES_DIR / ann_name

    saved = cv2.imwrite(
        str(ann_path),
        annotated,
    )

    if not saved:
        return AnalysisResult(
            success=False,
            message="Could not save the annotated image.",
            image_path=str(image_path),
            detections=detections,
            image_width=w,
            image_height=h,
        )

    message = (
        f"Detected {len(detections)} candidate seat/desk regions. "
        "These are proposals only - please review and correct "
        "before confirming."
    )

    return AnalysisResult(
        success=True,
        message=message,
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
    Estimate classroom rows and columns from detected candidates.

    The result is approximate and requires administrator review.
    """

    if not detections:
        return {
            "estimated_rows": target_rows or 0,
            "estimated_columns": target_cols or 0,
            "num_detections": 0,
            "note": (
                "No candidate regions detected. "
                "Please enter rows and columns manually."
            ),
        }

    ys = sorted(
        d.center_y
        for d in detections
    )

    row_threshold = max(
        30,
        image_height // 25,
    )

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

    estimated_cols = max(
        len(row)
        for row in rows_list
    )

    if target_rows is not None:
        estimated_rows = target_rows

    if target_cols is not None:
        estimated_cols = target_cols

    return {
        "estimated_rows": estimated_rows,
        "estimated_columns": estimated_cols,
        "num_detections": len(detections),
        "note": (
            "Grid estimate is approximate. "
            "Please verify the rows, columns, and seating capacity."
        ),
    }
