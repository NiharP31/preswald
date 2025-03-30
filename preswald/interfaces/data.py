import logging
from typing import Optional

import pandas as pd

from preswald.engine.service import PreswaldService


# Configure logging
logger = logging.getLogger(__name__)


def connect(headless=False):
    """
    Connect to the Preswald service or set up headless mode.
    
    Args:
        headless (bool): If True, enables headless mode (console output without server)
    """
    if headless:
        import os
        os.environ["PRESWALD_HEADLESS"] = "1"
        print("[Preswald] Running in headless mode (console output)")
    
    try:
        import os
        from preswald.engine.service import PreswaldService
        
        # For headless mode, we need to initialize with the script path
        if os.environ.get("PRESWALD_HEADLESS") == "1":
            script_path = os.environ.get("PRESWALD_SCRIPT_PATH")
            if script_path:
                service = PreswaldService.initialize(script_path)
            else:
                # Try to detect the calling script
                import inspect
                frame = inspect.currentframe()
                try:
                    caller_file = frame.f_back.f_globals.get('__file__')
                    if caller_file:
                        service = PreswaldService.initialize(os.path.abspath(caller_file))
                    else:
                        service = PreswaldService.get_instance()
                finally:
                    del frame
        else:
            # Normal mode - get existing instance
            service = PreswaldService.get_instance()
            
        source_names, duckdb_conn = service.data_manager.connect()
        logger.info(f"Successfully connected to data sources: {source_names}")
        return duckdb_conn
    except Exception as e:
        logger.error(f"Error connecting to datasources: {e}")


def query(sql: str, source_name: str) -> pd.DataFrame:
    """
    Query a data source using sql from preswald.toml by name
    """
    try:
        service = PreswaldService.get_instance()
        df_result = service.data_manager.query(sql, source_name)
        logger.info(f"Successfully queried data source: {source_name}")
        return df_result
    except Exception as e:
        logger.error(f"Error querying data source: {e}")


def get_df(source_name: str, table_name: Optional[str] = None) -> pd.DataFrame:
    """
    Get a dataframe from the named data source from preswald.toml
    If the source is a database/has multiple tables, you must specify a table_name
    """
    try:
        service = PreswaldService.get_instance()
        df_result = service.data_manager.get_df(source_name, table_name)
        logger.info(f"Successfully got a dataframe from data source: {source_name}")
        return df_result
    except Exception as e:
        logger.error(f"Error getting a dataframe from data source: {e}")
