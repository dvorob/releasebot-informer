#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Logging
"""
import logging.config


def setup():
    """
        Initialization logging system
    """
    logging.config.fileConfig('/etc/xerxes/logging_informer_new.conf')
    logger = logging.getLogger("informer")
    logger.propagate = False
    return logger
