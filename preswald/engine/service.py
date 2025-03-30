"""
Modified service module that selects appropriate implementation
based on environment (server or browser)
"""

import logging
import sys
import os


logger = logging.getLogger(__name__)

# Detect environment
IS_PYODIDE = "pyodide" in sys.modules

# Check if running in headless mode
# - Environment variable: PRESWALD_HEADLESS=1
# - Direct script execution: __name__ == "__main__" in calling script
IS_HEADLESS = os.environ.get("PRESWALD_HEADLESS") == "1"

if not IS_HEADLESS and not IS_PYODIDE:
    import inspect
    frame = inspect.currentframe()
    while frame:
        if frame.f_globals.get("__name__") == "__main__" and frame.f_code.co_filename != sys.modules['preswald.main'].__file__:
            # we are running as a script directly
            IS_HEADLESS = True
            logger.info("Detected direct script execution, setting headless mode")
            break
        frame = frame.f_back

# Import appropriate implementation based on environment
if IS_PYODIDE:
    # In browser (Pyodide) environment
    from preswald.browser.virtual_service import VirtualPreswaldService as ServiceImpl

    logger.info("Using VirtualPreswaldService (Browser/Pyodide environment)")
elif IS_HEADLESS:
    # In headless mode (plain Python script)
    from preswald.engine.script_service import ScriptService as ServiceImpl
    logger.info("Using ScriptService (Headless mode)")
else:
    # In regular Python environment with server capabilities
    from preswald.engine.server_service import ServerPreswaldService as ServiceImpl

    logger.info("Using ServerPreswaldService (Native Python environment)")


class PreswaldService:
    """
    Facade that forwards to the appropriate implementation based on environment.
    Maintains the same API regardless of environment.
    """

    @classmethod
    def initialize(cls, script_path=None):
        """Initialize the service"""
        return ServiceImpl.initialize(script_path)

    @classmethod
    def get_instance(cls):
        """Get the service instance"""
        return ServiceImpl.get_instance()
