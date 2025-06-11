"""
Utils package initialization file.
This file helps Python recognize this directory as a package.
It also provides path manipulation to fix import issues.
"""
import os
import sys

# Add project root to system path to ensure consistent imports
def fix_path():
    """Add necessary paths to sys.path for both absolute and relative imports to work"""
    # Get the path to the src directory
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Get the path to the project root
    project_root = os.path.dirname(src_dir)
    
    # Add both paths if they're not already there
    if src_dir not in sys.path:
        sys.path.append(src_dir)
    if project_root not in sys.path:
        sys.path.append(project_root)
        
    return {"src_dir": src_dir, "project_root": project_root}

# Fix the path when this package is imported
paths = fix_path()