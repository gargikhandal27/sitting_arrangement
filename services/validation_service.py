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


# ==================================================
# 1-CLICK SMART AUTO-CLEAN & REPAIR FUNCTIONS
# ==================================================

def repair_and_clean_students(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Automatically clean and repair student dataset:
    - Normalizes column headers and strips whitespace.
    - Drops completely empty rows.
    - Resolves missing required columns with safe fallbacks.
    - Resolves missing student_name with 'Student <roll_number>'.
    - Resolves missing batch with roll-number prefix or 'GENERAL'.
    - Deduplicates student_id and roll_number (keeps first occurrence).
    Returns (cleaned_df, list_of_actions_taken).
    """
    actions: List[str] = []
    df = _normalize_columns(df)

    initial_count = len(df)
    df = df.dropna(how="all").copy()
    dropped_empty = initial_count - len(df)
    if dropped_empty > 0:
        actions.append(f"Removed {dropped_empty} completely blank row(s).")

    # Ensure required columns exist
    for col in REQUIRED_STUDENT_COLUMNS:
        if col not in df.columns:
            if col == "student_id" and "roll_number" in df.columns:
                df["student_id"] = df["roll_number"]
                actions.append("Created missing 'student_id' column using roll numbers.")
            elif col == "roll_number" and "student_id" in df.columns:
                df["roll_number"] = df["student_id"]
                actions.append("Created missing 'roll_number' column using student IDs.")
            elif col == "batch":
                df["batch"] = "GENERAL"
                actions.append("Created missing 'batch' column with default 'GENERAL'.")
            else:
                df[col] = ""
                actions.append(f"Added missing required column: '{col}'.")

    # Keep only relevant columns
    df = df[REQUIRED_STUDENT_COLUMNS].copy()

    # Convert to string and clean whitespace
    for col in REQUIRED_STUDENT_COLUMNS:
        df[col] = df[col].fillna("").astype(str).str.strip()
        df.loc[df[col].str.lower() == "nan", col] = ""
        df.loc[df[col].str.lower() == "none", col] = ""

    # Drop rows that are completely empty across student_id, roll_number, student_name
    whitespace_empty_mask = (df["student_id"] == "") & (df["roll_number"] == "") & (df["student_name"] == "")
    whitespace_empty_count = int(whitespace_empty_mask.sum())
    if whitespace_empty_count > 0:
        df = df[~whitespace_empty_mask].copy()
        actions.append(f"Removed {whitespace_empty_count} blank row(s).")

    # Fix missing student_id
    missing_id_mask = df["student_id"] == ""
    missing_ids = int(missing_id_mask.sum())
    if missing_ids > 0:
        for idx in df[missing_id_mask].index:
            roll = df.at[idx, "roll_number"]
            df.at[idx, "student_id"] = f"STU_{roll}" if roll else f"STU_{idx + 1:04d}"
        actions.append(f"Auto-generated {missing_ids} missing student ID(s).")

    # Fix missing roll_number
    missing_roll_mask = df["roll_number"] == ""
    missing_rolls = int(missing_roll_mask.sum())
    if missing_rolls > 0:
        for idx in df[missing_roll_mask].index:
            sid = df.at[idx, "student_id"]
            df.at[idx, "roll_number"] = sid if sid else f"ROLL_{idx + 1:04d}"
        actions.append(f"Auto-generated {missing_rolls} missing roll number(s).")

    # Fix missing student_name
    missing_name_mask = df["student_name"] == ""
    missing_names = int(missing_name_mask.sum())
    if missing_names > 0:
        for idx in df[missing_name_mask].index:
            roll = df.at[idx, "roll_number"] or df.at[idx, "student_id"]
            df.at[idx, "student_name"] = f"Student {roll}"
        actions.append(f"Auto-filled {missing_names} missing student name(s) (e.g. 'Student <roll_number>').")

    # Fix missing or blank batch
    missing_batch_mask = df["batch"] == ""
    missing_batches = int(missing_batch_mask.sum())
    if missing_batches > 0:
        import re
        for idx in df[missing_batch_mask].index:
            roll = df.at[idx, "roll_number"]
            letters = re.findall(r"[A-Za-z]+", roll)
            inferred = letters[0].upper() if letters else "GENERAL"
            df.at[idx, "batch"] = inferred
        actions.append(f"Assigned default/inferred batches for {missing_batches} record(s).")

    # Normalize batch
    df["batch"] = df["batch"].str.upper().str.replace(" ", "_")

    # Deduplicate student_id (keep first)
    dup_id_count = int(df.duplicated(subset=["student_id"], keep="first").sum())
    if dup_id_count > 0:
        df = df.drop_duplicates(subset=["student_id"], keep="first").copy()
        actions.append(f"Removed {dup_id_count} duplicate record(s) matching existing student IDs.")

    # Deduplicate roll_number (keep first)
    dup_roll_count = int(df.duplicated(subset=["roll_number"], keep="first").sum())
    if dup_roll_count > 0:
        df = df.drop_duplicates(subset=["roll_number"], keep="first").copy()
        actions.append(f"Removed {dup_roll_count} duplicate record(s) matching existing roll numbers.")

    if not actions:
        actions.append("All records already look clean and valid.")

    return df, actions


def repair_and_clean_classrooms(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Automatically clean and repair classroom dataset:
    - Normalizes column headers and strips whitespace.
    - Resolves missing room_id or room_name.
    - Fixes non-numeric or missing rows/columns with sensible defaults (5 rows x 6 cols).
    - Deduplicates room_id (keeps first).
    Returns (cleaned_df, list_of_actions_taken).
    """
    actions: List[str] = []
    df = _normalize_columns(df)

    initial_count = len(df)
    df = df.dropna(how="all").copy()
    dropped_empty = initial_count - len(df)
    if dropped_empty > 0:
        actions.append(f"Removed {dropped_empty} completely blank row(s).")

    for col in REQUIRED_CLASSROOM_COLUMNS:
        if col not in df.columns:
            if col == "rows":
                df["rows"] = 5
                actions.append("Added missing 'rows' column with default value (5).")
            elif col == "columns":
                df["columns"] = 6
                actions.append("Added missing 'columns' column with default value (6).")
            elif col == "room_name" and "room_id" in df.columns:
                df["room_name"] = df["room_id"]
                actions.append("Filled missing 'room_name' using room IDs.")
            else:
                df[col] = ""

    if "is_available" not in df.columns:
        df["is_available"] = True

    # Numeric rows and columns
    for col, default_val in [("rows", 5), ("columns", 6)]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default_val).astype(int)
        invalid_mask = df[col] <= 0
        if invalid_mask.any():
            df.loc[invalid_mask, col] = default_val
            actions.append(f"Corrected non-positive numbers in '{col}' to default ({default_val}).")

    for col in ["room_id", "room_name"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # Drop rows that are completely blank across room_id and room_name
    whitespace_empty_mask = (df["room_id"] == "") & (df["room_name"] == "")
    whitespace_empty_count = int(whitespace_empty_mask.sum())
    if whitespace_empty_count > 0:
        df = df[~whitespace_empty_mask].copy()
        actions.append(f"Removed {whitespace_empty_count} blank classroom row(s).")

    # Missing room_id
    missing_id_mask = df["room_id"] == ""
    missing_ids = int(missing_id_mask.sum())
    if missing_ids > 0:
        for idx in df[missing_id_mask].index:
            df.at[idx, "room_id"] = f"R{idx + 1:02d}"
        actions.append(f"Auto-generated {missing_ids} missing room ID(s).")

    # Missing room_name
    missing_name_mask = df["room_name"] == ""
    missing_names = int(missing_name_mask.sum())
    if missing_names > 0:
        for idx in df[missing_name_mask].index:
            df.at[idx, "room_name"] = f"Classroom {df.at[idx, 'room_id']}"
        actions.append(f"Auto-filled {missing_names} missing room name(s).")

    df["is_available"] = df["is_available"].astype(str).str.lower().isin(["true", "1", "yes", "y"])

    # Deduplicate room_id
    dup_rooms = int(df.duplicated(subset=["room_id"], keep="first").sum())
    if dup_rooms > 0:
        df = df.drop_duplicates(subset=["room_id"], keep="first").copy()
        actions.append(f"Removed {dup_rooms} duplicate classroom record(s).")

    if not actions:
        actions.append("All classroom records look clean and valid.")

    return df, actions


def repair_and_clean_supervisors(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Automatically clean and repair supervisor dataset:
    - Normalizes column headers and strips whitespace.
    - Resolves missing supervisor_id or supervisor_name.
    - Deduplicates supervisor_id (keeps first).
    Returns (cleaned_df, list_of_actions_taken).
    """
    actions: List[str] = []
    df = _normalize_columns(df)

    initial_count = len(df)
    df = df.dropna(how="all").copy()
    dropped_empty = initial_count - len(df)
    if dropped_empty > 0:
        actions.append(f"Removed {dropped_empty} completely blank row(s).")

    for col in REQUIRED_SUPERVISOR_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    if "is_available" not in df.columns:
        df["is_available"] = True

    for col in ["supervisor_id", "supervisor_name"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # Drop rows that are completely blank across supervisor_id and supervisor_name
    whitespace_empty_mask = (df["supervisor_id"] == "") & (df["supervisor_name"] == "")
    whitespace_empty_count = int(whitespace_empty_mask.sum())
    if whitespace_empty_count > 0:
        df = df[~whitespace_empty_mask].copy()
        actions.append(f"Removed {whitespace_empty_count} blank supervisor row(s).")

    # Missing supervisor_id
    missing_id_mask = df["supervisor_id"] == ""
    missing_ids = int(missing_id_mask.sum())
    if missing_ids > 0:
        for idx in df[missing_id_mask].index:
            df.at[idx, "supervisor_id"] = f"SUP_{idx + 1:03d}"
        actions.append(f"Auto-generated {missing_ids} missing supervisor ID(s).")

    # Missing supervisor_name
    missing_name_mask = df["supervisor_name"] == ""
    missing_names = int(missing_name_mask.sum())
    if missing_names > 0:
        for idx in df[missing_name_mask].index:
            df.at[idx, "supervisor_name"] = f"Supervisor {df.at[idx, 'supervisor_id']}"
        actions.append(f"Auto-filled {missing_names} missing supervisor name(s).")

    df["is_available"] = df["is_available"].astype(str).str.lower().isin(["true", "1", "yes", "y"])

    # Deduplicate supervisor_id
    dup_sups = int(df.duplicated(subset=["supervisor_id"], keep="first").sum())
    if dup_sups > 0:
        df = df.drop_duplicates(subset=["supervisor_id"], keep="first").copy()
        actions.append(f"Removed {dup_sups} duplicate supervisor record(s).")

    if not actions:
        actions.append("All supervisor records look clean and valid.")

    return df, actions
