"""
Validation service for structured data imports.
"""
from typing import Dict, List, Any, Tuple
import pandas as pd


REQUIRED_STUDENT_COLUMNS = ["student_id", "roll_number", "student_name", "batch"]
REQUIRED_CLASSROOM_COLUMNS = ["room_id", "room_name", "rows", "columns"]
REQUIRED_SUPERVISOR_COLUMNS = ["supervisor_id", "supervisor_name"]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and lower-case column names for robust matching."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def validate_students(df: pd.DataFrame) -> Tuple[bool, List[str], pd.DataFrame]:
    """
    Validate student dataframe.
    Returns: (is_valid, list_of_errors, cleaned_df)
    """
    errors: List[str] = []
    df = _normalize_columns(df)

    # Required columns
    missing = [c for c in REQUIRED_STUDENT_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors, df

    # Keep only relevant columns + drop completely empty rows
    df = df[REQUIRED_STUDENT_COLUMNS].copy()
    df = df.dropna(how="all")

    if len(df) == 0:
        errors.append("File contains no student records.")
        return False, errors, df

    # Missing values
    for col in REQUIRED_STUDENT_COLUMNS:
        null_count = df[col].isna().sum()
        if null_count > 0:
            errors.append(f"Column '{col}' has {null_count} missing value(s).")

    # Convert to string and strip
    for col in REQUIRED_STUDENT_COLUMNS:
        df[col] = df[col].astype(str).str.strip()

    # Empty strings after strip
    for col in REQUIRED_STUDENT_COLUMNS:
        empty_count = (df[col] == "").sum() + (df[col].str.lower() == "nan").sum()
        if empty_count > 0:
            errors.append(f"Column '{col}' has {empty_count} empty value(s).")

    # Duplicate student_id
    dup_ids = df[df.duplicated(subset=["student_id"], keep=False)]["student_id"].unique()
    if len(dup_ids) > 0:
        errors.append(f"Duplicate student_id(s): {', '.join(map(str, dup_ids[:10]))}"
                      + (" ..." if len(dup_ids) > 10 else ""))

    # Duplicate roll_number (warning-level, but we treat as error for cleanliness)
    dup_rolls = df[df.duplicated(subset=["roll_number"], keep=False)]["roll_number"].unique()
    if len(dup_rolls) > 0:
        errors.append(f"Duplicate roll_number(s): {', '.join(map(str, dup_rolls[:10]))}"
                      + (" ..." if len(dup_rolls) > 10 else ""))

    # Normalize batch names (simple clean)
    df["batch"] = df["batch"].str.upper().str.replace(" ", "_")

    is_valid = len(errors) == 0
    return is_valid, errors, df


def validate_classrooms(df: pd.DataFrame) -> Tuple[bool, List[str], pd.DataFrame]:
    errors: List[str] = []
    df = _normalize_columns(df)

    missing = [c for c in REQUIRED_CLASSROOM_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors, df

    # Optional is_available
    if "is_available" not in df.columns:
        df["is_available"] = True

    cols = REQUIRED_CLASSROOM_COLUMNS + ["is_available"]
    df = df[cols].copy()
    df = df.dropna(how="all")

    if len(df) == 0:
        errors.append("File contains no classroom records.")
        return False, errors, df

    for col in ["room_id", "room_name"]:
        df[col] = df[col].astype(str).str.strip()

    # Numeric checks
    for col in ["rows", "columns"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if df[col].isna().any():
            errors.append(f"Column '{col}' contains non-numeric or missing values.")
        elif (df[col] <= 0).any():
            errors.append(f"Column '{col}' must be positive integers.")

    # is_available
    df["is_available"] = df["is_available"].astype(str).str.lower().isin(["true", "1", "yes", "y"])

    # Duplicate room_id
    dup = df[df.duplicated(subset=["room_id"], keep=False)]["room_id"].unique()
    if len(dup) > 0:
        errors.append(f"Duplicate room_id(s): {', '.join(map(str, dup))}")

    is_valid = len(errors) == 0
    return is_valid, errors, df


def validate_supervisors(df: pd.DataFrame) -> Tuple[bool, List[str], pd.DataFrame]:
    errors: List[str] = []
    df = _normalize_columns(df)

    missing = [c for c in REQUIRED_SUPERVISOR_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors, df

    if "is_available" not in df.columns:
        df["is_available"] = True

    cols = REQUIRED_SUPERVISOR_COLUMNS + ["is_available"]
    df = df[cols].copy()
    df = df.dropna(how="all")

    if len(df) == 0:
        errors.append("File contains no supervisor records.")
        return False, errors, df

    for col in ["supervisor_id", "supervisor_name"]:
        df[col] = df[col].astype(str).str.strip()

    df["is_available"] = df["is_available"].astype(str).str.lower().isin(["true", "1", "yes", "y"])

    dup = df[df.duplicated(subset=["supervisor_id"], keep=False)]["supervisor_id"].unique()
    if len(dup) > 0:
        errors.append(f"Duplicate supervisor_id(s): {', '.join(map(str, dup))}")

    is_valid = len(errors) == 0
    return is_valid, errors, df
