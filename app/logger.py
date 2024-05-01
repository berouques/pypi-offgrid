import logging
import os
import coloredlogs
from flask.logging import default_handler

def get_logger(workdir, log_file_name):
    """Configure the root logger for color output and file logging with a standard format"""
    
    path =  os.path.normpath( os.path.join(workdir, log_file_name))
    
    # Clear existing handlers on the root logger to prevent duplicates
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Remove the default Flask logger
    root_logger.removeHandler(default_handler)

    # Set the logging level for the root logger
    root_logger.setLevel(logging.DEBUG)

    # Define styles for colored logs
    field_styles = {'asctime': {'color': 'green'}, 'levelname': {'color': 'white', 'bold': True},
                    'filename': {'color': 'magenta'}, 'lineno': {'color': 'cyan'}, 'funcName': {'color': 'blue'}}
    level_styles = {'debug': {'color': 'cyan'}, 'info': {'color': 'green'}, 'warning': {'color': 'yellow'},
                    'error': {'color': 'red'}, 'critical': {'color': 'white', 'background': 'red'},
                    'notice': {'color': 'magenta'}, 'spam': {'color': 'green', 'faint': True},
                    'success': {'color': 'green', 'bold': True}, 'verbose': {'color': 'blue'}}

    # Define a standard formatter
    formatter = logging.Formatter("%(asctime)s %(levelname).8s | %(message)s", "%H:%M:%S")

    # Create handlers for logging to file and console
    file_handler = logging.FileHandler(path)
    console_handler = logging.StreamHandler()

    # Set the formatter for each handler
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Install colored logs for the console handler
    coloredlogs.install(level='DEBUG', logger=root_logger, fmt="%(asctime)s %(levelname).8s | %(message)s",
                        datefmt="%H:%M:%S", field_styles=field_styles, level_styles=level_styles, stream=console_handler.stream)

    # Log a startup message
    root_logger.debug("\n" * 6 + "-" * 40 + "\nstarting the application\n")

    # Return the configured logger
    return root_logger
