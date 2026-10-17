import importlib.util
from pathlib import Path
def load_manager():
 p=Path(__file__).resolve().parent/'manage-user.py';s=importlib.util.spec_from_file_location('manager',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
