import sys
from pathlib import Path

# Ensure project root is importable regardless of how Streamlit is launched
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from services.api.health import get_health_status

st.title("ATS Resume Generator")

st.subheader("System status")
status = get_health_status()
st.json(status)