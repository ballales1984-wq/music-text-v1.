"""
Pytest configuration per i test.
Aggiunge il percorso backend al path Python.
"""
import sys
from pathlib import Path

# Aggiungi la directory backend al path Python
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))