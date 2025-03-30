# Initialize the Preswald package
__version__ = "0.1.48"


# Import to trigger headless detection early
from .utils import detect_script_execution

from . import interfaces as _interfaces
from .interfaces import *  # noqa: F403

__all__ = _interfaces.__all__
