#!/usr/bin/env python
import sys
import os

# Ajouter src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Vérifier que le chemin est bien ajouté
print("sys.path:", sys.path[:3])

# Lancer pytest avec tests skills
import pytest
pytest.main(['-v', 'tests/skills', 'tests/abilities'])
