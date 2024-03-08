"""
Utility functions for the imageautomation package.

Classes:

    PrintLog
    ColorPrint
    Configuration

Functions:

    None

Variables:

    None

Global Variables (via config):

    config.quiet : bool
        Suppress progress bar output (default False)

"""

# History
# 2024-03-06  Add PrintLog extension of ColorPrint
# 2024-03-06  First version (subset fromfootball.py core 1.4)

# TODO
# None

#
# Import libraries
#

# General
import yaml
from colorama import Fore, Style
import pathlib

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
    TODO: Add description
    """
    @staticmethod
    def print_yellow(message):
        """Prints a message in yellow"""
        print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

    @staticmethod
    def print_red(message):
        """Prints a message in red"""
        print(f"{Fore.RED}{message}{Style.RESET_ALL}")

    def error(message):
        """Prints a message in red and logs an error"""
        if not config.quiet:
            PrintLog.print_red(message)  # Fix: Remove 'self' and call PrintLog.print_red()
        logger.error(message)

    def warning(message):
        """Prints a message in yellow and logs a warning"""
        if not config.quiet:
            PrintLog.print_yellow(message)  # Fix: Remove 'self' and call PrintLog.print_yellow()
        logger.warning(message)

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
