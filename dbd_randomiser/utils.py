"""
Utility functions for formatting perk filenames into display names.
"""

import os
import re

def format_perk_name(filename: str) -> str:
    """
    Convert a filename (e.g. 'DeadHard.png' or 'dead_hard.png')
    into a human-readable uppercase name with spaces:
    'DEAD HARD'.
    """
    name, _ext = os.path.splitext(filename)
    # Replace underscores and insert spaces before capital letters
    name = name.replace('_', ' ')
    name = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
    return name.upper()
