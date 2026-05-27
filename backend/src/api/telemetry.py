import os
import logging
from azure.monitor.opentelemetry import configure_azure_monitor

# create a dedicated logger for telemetry
logger = logging.getLogger("compliance-telemetry")

def setup_telemetry():
    """
    Initializes Azure Monitor telemetry with OpenTelemetry integration.
    Tracks HTTP requests, database queries, errors, perfromace metrics
    Sends this data to azure monitor
    """

    # retrieve connection string 
    connection_string = os.getenv("AZURE_MONITOR_CONNECTION_STRING")
    if not connection_string:
        logger.warning(" No instrumentation key found. Telemetry will be disabled.")
        return

    try:
        configure_azure_monitor(connection_string=connection_string,
                                logger_name="compliance-telemetry")
        logger.info("Azure Monitor Tracking Enabled and Connected.")
    except Exception as e:
        logger.error(f"Failed to initialize Azure Monitor : {e}")