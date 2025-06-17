import streamlit as st
from pathlib import Path
import json
import pandas as pd
import settings

def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

def scan_for_data_files():
    base_dir = Path(__file__).parent
    data_dir = base_dir / settings.DEFAULT_DATA_DIR

    if not data_dir.exists():
        st.sidebar.warning(f"Default data directory not found: {data_dir}")
        return {}

    files = list(data_dir.glob(settings.FILE_PATTERN))

    if not files:
        st.sidebar.warning(f"No JSON files found in: {data_dir}")
        return {}

    key = {
        "name": lambda f: f.name,
        "mtime": lambda f: f.stat().st_mtime,
        "ctime": lambda f: f.stat().st_ctime,
    }.get(settings.SORT_FILES_BY, lambda f: f.name)

    reverse = settings.SORT_ORDER == "descending"
    sorted_files = sorted(files, key=key, reverse=reverse)

    return {f.name: [f, f.stat().st_size] for f in sorted_files}

def format_file_name(name, size):
    name = Path(name).stem
    name = name.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in name.split()) + f" ({sizeof_fmt(size)})"

def prepare_step_range(last_step, num_steps, max_step_index):
    start_step = max(0, last_step - num_steps)
    end_step = min(last_step, max_step_index)
    return (start_step, end_step, 1)

@st.cache_data(ttl=settings.CACHE_TTL, show_spinner="Loading data...")
def load_json_file(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

@st.cache_data(ttl=settings.CACHE_TTL, show_spinner="Loading data...")
def load_uploaded_data(uploaded_file):
    return json.load(uploaded_file)

@st.cache_data(ttl=settings.CACHE_TTL)
def get_available_plots(scan_data):
    all_steps = scan_data.get("steps", [])
    return [
        cfg for cfg in settings.PLOT_CONFIGS
        if cfg["items_key"] in scan_data and any(cfg["value_key"] in step for step in all_steps)
    ]
