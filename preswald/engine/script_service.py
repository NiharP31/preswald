"""
Script service module for running Preswald scripts in headless mode (as plain Python scripts).
This allows running Preswald apps without a server or UI components.
"""

import logging
import os
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ScriptService:
    """
    Service implementation for running Preswald scripts in headless mode.
    Provides CLI output for components instead of rendering in a web UI.
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def initialize(cls, script_path=None):
        """Initialize the script service singleton"""
        if cls._instance is None:
            cls._instance = cls()
            if script_path:
                cls._instance._script_path = script_path
                cls._instance._initialize_data_manager(script_path)
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Get the service instance, creating it if necessary"""
        if cls._instance is None:
            raise RuntimeError(
                "ScriptService not initialized. Did you call initialize()?"
            )
        return cls._instance

    def __init__(self):
        """Initialize the script service with necessary state"""
        # Component state management
        self._component_states = {}
        self._lock = threading.Lock()
        
        # Track rendered components
        self._rendered_components = []
        
        # Data and branding management (for compatibility)
        self.data_manager = None
        self.branding_manager = None
        
        # Script path
        self._script_path = None
        
        # For API compatibility
        self._is_shutting_down = False
        self.websocket_connections = {}
        self.script_runners = {}

        logger.info("Initialized ScriptService for headless mode")

    @property
    def script_path(self) -> Optional[str]:
        """Get the current script path"""
        return self._script_path

    @script_path.setter
    def script_path(self, path: str):
        """Set script path and initialize necessary components"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Script not found: {path}")

        self._script_path = path
        self._initialize_data_manager(path)

    def append_component(self, component):
        """
        Process a component in headless mode by printing it to console
        rather than storing for web rendering.
        """
        try:
            # Store the component for potential future use
            self._rendered_components.append(component)
            
            # Print the component to console based on its type
            self._print_component(component)
            
            # Update component state if it has an ID and value
            if isinstance(component, dict) and "id" in component and "value" in component:
                with self._lock:
                    self._component_states[component["id"]] = component["value"]
                    
        except Exception as e:
            logger.error(f"Error processing component in headless mode: {e}", exc_info=True)

    def _print_component(self, component):
        """Format and print a component to the console based on its type"""
        if isinstance(component, str):
            # Handle raw HTML/text
            print(f"[html] {component}")
            return
            
        if not isinstance(component, dict):
            print(f"[unknown] {str(component)}")
            return
            
        component_type = component.get("type")
        
        if component_type == "text":
            # Print markdown text
            print(f"[text] {component.get('markdown', '')}")
            
        elif component_type == "slider":
            # Print slider with its current value
            label = component.get("label", "")
            value = component.get("value", "")
            print(f"[slider] {label}: {value}")
            
        elif component_type == "plot":
            # Just acknowledge that a plot would be shown
            print(f"[plot] Plot would be displayed in browser mode")
            
        elif component_type == "table":
            # Print table rows count
            data = component.get("data", [])
            title = component.get("title", "Table")
            print(f"[table] {title} ({len(data)} rows)")
            
        elif component_type == "checkbox":
            # Print checkbox state
            label = component.get("label", "")
            value = component.get("value", False)
            print(f"[checkbox] {label}: {'✓' if value else '✗'}")
            
        elif component_type == "selectbox":
            # Print select box options and current value
            label = component.get("label", "")
            value = component.get("value", "")
            print(f"[selectbox] {label}: {value}")
            
        else:
            # Generic fallback for unknown component types
            component_id = component.get("id", "unknown")
            print(f"[{component_type}] Component ID: {component_id}")

    def get_rendered_components(self):
        """Return rendered components in a format compatible with ServerPreswaldService."""
        return {"rows": self._rendered_components}

    def get_component_state(self, component_id: str, default: Any = None) -> Any:
        """Get the current state of a component"""
        with self._lock:
            value = self._component_states.get(component_id, default)
            logger.debug(f"[STATE] Getting state for {component_id}: {value}")
            return value

    def clear_components(self):
        """Clear all components"""
        self._rendered_components = []

    async def register_client(self, client_id: str, *args, **kwargs):
        """Stub for API compatibility with ServerPreswaldService."""
        logger.debug(f"Client registration ignored in headless mode: {client_id}")
        return None  # No script runner in headless mode

    async def unregister_client(self, client_id: str):
        """Stub for API compatibility with ServerPreswaldService."""
        pass

    async def handle_client_message(self, client_id: str, message: Dict[str, Any]):
        """Handle component updates in headless mode."""
        if message.get("type") == "component_update":
            states = message.get("states", {})
            with self._lock:
                for component_id, value in states.items():
                    self._component_states[component_id] = value
                    logger.debug(f"Updated component state: {component_id} = {value}")

    async def shutdown(self):
        """Gracefully shut down the service"""
        self._is_shutting_down = True
        logger.info("Script service shutting down...")

    def _initialize_data_manager(self, script_path: str) -> None:
        """Initialize the data manager with the script path"""
        try:
            script_dir = os.path.dirname(script_path)
            preswald_path = os.path.join(script_dir, "preswald.toml")
            secrets_path = os.path.join(script_dir, "secrets.toml")

            # Reuse the DataManager implementation
            from preswald.engine.managers.data import DataManager
            self.data_manager = DataManager(
                preswald_path=preswald_path, secrets_path=secrets_path
            )
        except Exception as e:
            logger.error(f"Error initializing data manager: {e}", exc_info=True)
            # Create empty data manager to avoid errors
            from preswald.engine.managers.data import DataManager
            self.data_manager = DataManager()