
import sys
import os

# Add the project root to sys.path to ensure absolute imports work correctly
# This is useful when running the script directly from the src directory or other contexts
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.ui.oper_window import run_app

if __name__ == "__main__":
    run_app()
