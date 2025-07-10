import os
import re

def format_perk_name(filename: str) -> str:
    """
    Convert e.g. 'DeadHard.png' or 'dead_hard.png'
    into 'DEAD HARD'.
    """
    name, _ = os.path.splitext(filename)
    name = name.replace('_',' ')
    name = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
    return name.upper()
