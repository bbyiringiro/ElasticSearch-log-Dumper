#!/usr/bin/python

import errno
import logging
import os

from config import LOG_LEVEL

# Instantiate a logger to log all errors
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define how we format our log messages
fmt_ch = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')

# Create a handler that outputs logs events with
# severity level LOG_LEVEL and above to sys.stderr
ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)
ch.setFormatter(fmt_ch)

# Add handlers to logger
logger.addHandler(ch)
