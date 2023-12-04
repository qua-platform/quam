from .quam_classes import *


# Exec statement needed to trick Pycharm type checker into recognizing it as a dataclass
# This will no longer be necessary once we drop support for Python 3.9
# We also do this at the end of quam_classes.py, but PyCharm also requires it here
_quam_dataclass = quam_dataclass
from dataclasses import dataclass as quam_dataclass

exec("quam_dataclass = _quam_dataclass")
