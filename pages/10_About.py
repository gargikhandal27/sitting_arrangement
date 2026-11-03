"""
About / Settings page
"""
import streamlit as st

st.title("ℹ️ About")
st.markdown("Project information and AI components.")
st.divider()


st.markdown("""
### Multimodal AI-Based Examination Seating Arrangement and Supervisor Allotment System

**Developed for**: B.Tech Computer Science Engineering – AI Course Project

#### AI Components
| Component | Technique | Purpose |
|-----------|-----------|---------|
| Structured Data | Pandas + Validation | Clean student, classroom, supervisor records |
| Computer Vision | OpenCV (+ optional lightweight detector) | Extract seat layouts from classroom images |
| Natural Language | Controlled parser → structured config | Interpret administrator instructions |
| Constraint Optimization | Google OR-Tools CP-SAT | Generate valid seating & supervisor plans |
| Verification | Independent rule engine | Guarantee hard constraints are satisfied |

#### Design Principles
- No paid APIs or cloud dependencies
- Manual fallbacks always available
- Administrator confirmation required for NLP & image results
- Hard constraints are never silently relaxed
- Independent verification of every plan

#### Current Development Phase
**Phase 2** – Navigation & UI skeleton complete.
""")

st.divider()
st.caption("Built incrementally. Each phase is tested before proceeding.")
