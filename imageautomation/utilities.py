"""
Utility functions for the imageautomation package.

Classes:

    PrintLog
    ColorPrint
    Configuration

Functions:

    run_subprocess

Variables:

    None

Global Variables (via config):

    config.quiet : bool
        Suppress progress bar output (default False)

    config.exit_code : int
        Exit code for the application (default 0)

    config.exit_reason : str
        Reason for the exit code

"""

# History
# 2024-03-11  Add exit_code and exit_reason to config
# 2024-03-11  Add critical method to PrintLog
# 2024-03-11  Add exception for rm in run_subprocess
# 2024-03-11  Add run_subprocess
# 2024-03-06  Add PrintLog extension of ColorPrint
# 2024-03-06  First version (subset from football.py core 1.4)

# TODO
# None

#
# Import libraries
#

# General
import yaml
from colorama import Fore, Style
import pathlib
import subprocess

# TUI progress bar

# Logging
from loguru import logger

# Config for global variables
import config


#
# Define classes
#


class PrintLog:
    """
    A class to print messages in different colors and log them.

    Attributes:
    
            None

    Methods:

        print_yellow(message):
            Prints a message in yellow

        print_red(message):
            Prints a message in red

        error(message):
            Prints a message in red and logs an error

        warning(message):
            Prints a message in yellow and logs a warning

        debug(message):
            Logs a debug message

        success(message):
            Logs a success message
    """
    @staticmethod
    def print_yellow(message):
        """Prints a message in yellow"""
        print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

    @staticmethod
    def print_red(message):
        """Prints a message in red"""
        print(f"{Fore.RED}{message}{Style.RESET_ALL}")

    def critical(message):
        """Prints a message in red and logs a critical error"""
        if not config.quiet:
            PrintLog.print_red(message)  
        logger.critical(message)
        config.exit_code = 1

    def error(message):
        """Prints a message in red and logs an error"""
        if not config.quiet:
            PrintLog.print_red(message)  # Fix: Remove 'self' and call PrintLog.print_red()
        logger.error(message)
        config.exit_code = 2

    def warning(message):
        """Prints a message in yellow and logs a warning"""
        if not config.quiet:
            PrintLog.print_yellow(message)  # Fix: Remove 'self' and call PrintLog.print_yellow()
        logger.warning(message)

    def info(message):
        """Logs an info message"""
        logger.info(message)

    def debug(message):
        """Logs a debug message"""
        logger.debug(message)

    def success(message):
        """Logs a success message"""
        logger.success(message)


class Configuration:
    """
    A class to represent the app configuration.

    Attributes:

        source : str
            Where to find the config file

    Methods:

        get():
            Retrieve, load, and returns the full config file as a dictionary

        device_trackers():
            Return just the device_trackers section of the config file dictionary

        api(api_name='all'):
            Return the full apis section of the config file dictionary or just the specified api

    """

    @logger.catch
    def __init__(self):
        """Constructs all necessary attributes for the Config object."""
        self.source = f"{pathlib.Path(__file__).parent.parent.absolute() / 'config.yaml'}"

    @logger.catch
    def get(self):
        """Retrieve, load, and returns the full config file"""

        with open(self.source, "r") as file:
            configuration = yaml.safe_load(file)

        return configuration

    @logger.catch
    def get_section(self, section, subsection="all"):
        """
        Return a section of the config file dictionary or just the specified subsection

        Parameters:

            section : str
                The section of the confg file dictionary to return
            subsection : str
                Optional subsection of the section to return instead
                default: 'all' (return the whole section of the config file)
        """

        if subsection == "all":
            return self.get().get(section)
        else:
            configuration = self.get()
            return configuration.get(section, {}).get(subsection)

#
# Define functions
#
        
def run_subprocess(application, command, success_message=None, error_message=None):
    """
    Run a subprocess command and return the output.

    Parameters:

        application : str
            The name of the application for display purposes

        command : list
            The command to run as a list of strings
        
        success_message : str
            Optional message to PrintLog if the command is successful
            default: None

        error_message : str
            Optional message to PrintLog if the command is unsuccessful
            default: None

    """
    try:
        _ = subprocess.run( 
            command,
            check=True,
            capture_output=True,
        )

    except FileNotFoundError as exc:
        PrintLog.error(
            f"{error_message}\n"
            f"The {application} executable could not be found\n{exc}\n"
            f"Please ensure that {application} is installed and the convert executable is in your PATH.\n"
            f"{exc.stderr.decode() if hasattr(exc, 'stderr') else ''}"
        )
        return False

    except subprocess.CalledProcessError as exc:
        if application == "rm":
            PrintLog.debug(
                f"{error_message}\n"
                f"{application} did not return a successful return code. "
                f"Returned {exc.returncode}\n{exc}\n"
                f"{exc.stderr.decode() if hasattr(exc, 'stderr') else ''}"
            )
            return True

        PrintLog.error(
            f"{error_message}\n"
            f"{application} did not return a successful return code. "
            f"Returned {exc.returncode}\n{exc}\n"
            f"{exc.stderr.decode() if hasattr(exc, 'stderr') else ''}"
        )
        return False

    except subprocess.TimeoutExpired as exc:
        PrintLog.error(
            f"{error_message}\n"
            f"{application} process timed out.\n{exc}/n"
            f"{exc.stderr.decode() if hasattr(exc, 'stderr') else ''}"
        )
        return False

    PrintLog.debug(success_message)    
    return True