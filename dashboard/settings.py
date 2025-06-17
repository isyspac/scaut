import os
from pathlib import Path

# Plot configurations
PLOT_CONFIGS = [
    {"name": "Meters", "items_key": "meters", "value_key": "meter_data",
     "limits_key": "meter_ranges", "errors_key": "meter_errors"},
    {"name": "Motors", "items_key": "motors", "value_key": "motor_values",
     "limits_key": "motor_ranges", "errors_key": "motor_errors"},
    {"name": "Checks", "items_key": "checks", "value_key": "check_data",
     "limits_key": "check_ranges", "errors_key": "check_errors"}
]

# Default values
DEFAULT_NUM_STEPS = 7
DEFAULT_FIG_WIDTH = 16
DEFAULT_FIG_HEIGHT_PER_PLOT = 4
CACHE_TTL = 3600  # 1 hour cache

# Default data settings
DEFAULT_DATA_DIR = "../data"
FILE_PATTERN = "prod/*.json"  # Pattern to match JSON files
SORT_FILES_BY = "mtime"  # Options: 'name', 'mtime' (modification time), 'ctime' (creation time)
SORT_ORDER = "ascending"  # Options: 'ascending', 'descending'

# Default functions
GET_FUNC = lambda x: 0  # Default function to get data from the file
PUT_FUNC = lambda x, y: y  # Default function to put data into the file
VERIFY_MOTOR = False  # Whether to verify motor values
DELAY = 0.1  # Delay in seconds for operations
TOLERANCE = 1e-3  # Tolerance for motor value comparisons
MAX_TRIES = 3  # Maximum number of tries for operations
PARALLEL = True  # Whether to run operations in parallel
SAMPLE_SIZE = 1   # Sample size for operations
MAX_RETRIES = 5  # Maximum retries for operations