# -*- coding: utf-8 -*-

"""
This file contains Flask config
"""

import os

DEBUG = False if os.environ.get("PYSERVICE_REGISTRY") == 'False' else True

# --------------------------------------------------------------------------
# Limiter
# --------------------------------------------------------------------------
RATELIMIT_STORAGE_URL = "memory://"
