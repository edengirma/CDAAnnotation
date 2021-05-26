#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 02/06/17 at 2:26 PM

@author: neil

Program description here

Version 0.0.0
"""
from astropy import units as u
import numpy as np
import os

__location__ = os.path.realpath(os.path.join(os.getcwd(),
                                             os.path.dirname(__file__)))

# =============================================================================
# Define variables
# =============================================================================
UUNIT = u.core.Unit
UQUANT = u.quantity.Quantity

stilts_jar_path = __location__ + '/stilts.jar'
STILTS = 'java -jar %s' % (stilts_jar_path)
