# Multimodal AI-Based Examination Seating Arrangement and Supervisor Allotment System

B.Tech Computer Science Engineering – AI Course Project

Combines **structured data**, **computer vision**, and **natural-language processing** with **constraint optimization** to generate examination seating plans and supervisor allocations.

---

## Current Status – Project Complete (Phases 1–14)

| Phase | Component | Status |
|-------|-----------|--------|
| 1 | Environment & structure | ✅ |
| 2 | Streamlit multi-page UI | ✅ |
| 3 | Database (SQLAlchemy + SQLite) | ✅ |
| 4 | Structured data import & validation | ✅ |
| 5 | Classroom layout representation | ✅ |
| 6 | Computer Vision prototype (OpenCV) | ✅ |
| 7 | Natural Language interpreter | ✅ |
| 8 | Seating optimization (OR-Tools CP-SAT) | ✅ |
| 9 | Supervisor allocation | ✅ |
| 10 | Independent verification | ✅ |
| 11 | Multimodal integration polish | ✅ |
| 12 | Reports & history | ✅ |
| 13 | Automated tests | ✅ |
| 14 | Documentation | ✅ |

---

## Architecture (Simple Explanation)

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Structured     │   │  Classroom       │   │  Natural        │
│  Data (CSV/XLSX) │   │  Images (CV)    │   │  Language (NLP) │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │  Unified Config +   │
                    │  Confirmed Layouts  │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  OR-Tools CP-SAT    │
                    │  Seating Solver     │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  Supervisor         │
                    │  Allocation         │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  Independent        │
                    │  Verification       │
                    └──────────┬──────────┘
                               ▼
                    Visualization + Reports
```

---

## AI / Technical Components

### 1. Structured Data Processing
- Pandas + custom validation
- Detects missing columns, duplicates, invalid values
- Saves clean records to SQLite

### 2. Computer Vision (Phase 6)
- **Library**: OpenCV (`opencv-python-headless`)
- **Method**: Grayscale → Gaussian blur → Canny edges → Contour filtering (area + aspect ratio)
- Output = candidate seat/desk bounding boxes
- **Important**: Detections are only proposals. Administrator must review and confirm.
- Manual grid creation is always available as a reliable fallback.
- No large neural network, no GPU, no internet required after install.

### 3. Natural Language Processing (Phase 7)
- Controlled, rule-based parser (regular expressions + keyword patterns)
- No paid LLM API
- Extracts: number of students, adjacency mode, minimize classrooms, supervisor ratio, time limit
- Shows interpretation, warnings, unsupported requests
- Requires explicit administrator confirmation

### 4. Constraint Optimization (Phase 8)
- **Solver**: Google OR-Tools CP-SAT
- Decision variables: student–seat assignment
- Hard constraints:
  - Each student exactly one seat
  - Each seat at most one student
  - Only available seats
  - Same-batch students not adjacent (horizontal or horizontal+vertical)
- Optional objective: minimize number of classrooms used
- Statuses handled correctly: OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN, MODEL_INVALID

### 5. Supervisor Allocation (Phase 9)
- Policy: `required = ceil(students_in_room / students_per_supervisor)`
- Only available supervisors
- No double-booking
- Shortages reported clearly

### 6. Independent Verification (Phase 10)
- Re-checks every hard constraint
- Does **not** trust the solver status
- Returns structured pass/fail report with violations

---

## How to Run

```bash
cd exam-allocation-system
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### Run tests
```bash
python -m pytest -v
```

---

## Recommended Demo Flow (for viva)

1. **Data Management** → Import sample students, classrooms, supervisors
2. **Classroom Layout Management** → Create a manual grid (or try Image Analysis)
3. **Natural Language Requirements** → Paste example instruction → Interpret → Confirm
4. **Seating Generation** → Run solver → show status & assignments
5. **Supervisor Allocation** → Allocate supervisors
6. **Verification** → Run independent checks → show all passed
7. **Seating Visualization** → Show coloured grid with roll numbers
8. **Reports & History** → Generate and download Excel reports

---

## Limitations (be honest in viva)

- OpenCV contour detection works best on clear floor-plans / top-down images; perspective photos need manual correction.
- NLP parser supports only a controlled set of requirements; arbitrary English is not fully understood.
- Solver performance depends on instance size and time limit; very large or tightly constrained instances may return UNKNOWN or INFEASIBLE.
- No diagonal adjacency rule in the current version (can be added later).
- Image analysis does not automatically create the final seat grid; it assists the administrator.

---

## Project Structure

```
exam-allocation-system/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── database/          # SQLAlchemy models & connection
├── models/
├── services/          # Business logic + AI components
├── solvers/           # OR-Tools seating + supervisor solvers
├── pages/             # Streamlit multi-page UI
├── tests/             # Pytest suite
├── data/
│   ├── templates/
│   ├── sample/
│   ├── classroom_images/
│   └── generated_reports/
└── artifacts/
```

---

## Viva Quick Points

- **Why multimodal?** Real exam administration involves tables, room photos, and verbal/written instructions. The system extracts useful information from each and combines them.
- **Why OR-Tools?** Constraint satisfaction with optional optimization; exact methods with clear status codes; no training data required.
- **Why rule-based NLP first?** Transparent, offline, no API cost, easy to validate and explain. Schema validation + human confirmation prevents silent errors.
- **Why independent verification?** Solver bugs or modelling mistakes should not produce an “approved” invalid plan.
- **What would you improve next?** Better CV (optional lightweight detector), richer NLP, diagonal separation, multi-session scheduling, larger-scale benchmarks.

---

Built incrementally, phase by phase, with testing and clear separation of AI components.
