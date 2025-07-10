# temp_qos_code/common_logger.py
# CHIMera QOS - Phase 1 - Rudimentary SHMS Logger Utility

import logging
import sys # To ensure output to stdout for basic setups

# --- Basic Logger Configuration ---

LOG_FORMAT = '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# To prevent adding multiple handlers to the same logger instance if get_qos_logger is called multiple times
_loggers_configured = {}

def get_qos_logger(service_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Provides a pre-configured Python logger for QOS services.
    In Phase 1, this directs logs to stdout.

    Args:
        service_name: The name of the service that will use this logger.
                      This will be part of the log message format.
        level: The minimum logging level for this logger instance.

    Returns:
        A configured logging.Logger instance.
    """
    logger_name = f"CHIMeraQOS.{service_name}"
    logger = logging.getLogger(logger_name)

    if logger_name not in _loggers_configured:
        logger.setLevel(level)

        # Ensure we don't add handlers if they already exist from a previous call
        # or if the logger already has handlers (e.g. from root logger config)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            # Prevent messages from being passed to the root logger if it also has handlers
            # This helps avoid duplicate messages if root is configured elsewhere.
            # However, for simple stdout, this might not be strictly necessary if only this configures.
            logger.propagate = False

        _loggers_configured[logger_name] = True
    else:
        # If logger was already configured, ensure its level is set (could be changed)
        logger.setLevel(level)

    return logger

# --- Example Usage (would be in other service files) ---
if __name__ == "__main__":
    print("Testing common_logger utility...")

    # Simulate how different services would get and use the logger
    qhal_logger = get_qos_logger("QHALService", level=logging.DEBUG)
    aes_logger = get_qos_logger("AEService") # Defaults to INFO
    rms_logger = get_qos_logger("RMService")

    qhal_logger.debug("QHAL debug message: Qubit q0 calibrated.")
    qhal_logger.info("QHAL info: Driver for 'SimQPU_1' registered.")

    aes_logger.info("AES info: Job 'job_123' submitted.")
    aes_logger.warning("AES warning: Job 'job_123' has high qubit requirement.")

    rms_logger.info("RMS info: 5 qubits allocated to job 'job_123'.")
    rms_logger.error("RMS error: Failed to allocate resources for job 'job_456'.")

    # Test getting logger again, should not add duplicate handlers
    qhal_logger_2 = get_qos_logger("QHALService", level=logging.INFO) # Change level to test
    qhal_logger_2.info("QHAL second info message via logger_2 (level changed).")
    qhal_logger_2.debug("This QHAL debug message via logger_2 should NOT appear if level was raised to INFO.")

    # Test propagation if root logger was also configured (not done here, so propagate=False is key)
    # logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    # root_test_logger = get_qos_logger("RootTest")
    # root_test_logger.info("This message should appear once.")

    print("\nTest complete. Check console output for correctly formatted and non-duplicated log messages.")
```
