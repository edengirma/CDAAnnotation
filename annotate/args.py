import sys
import argparse
from datetime import datetime


def args_setup():
    parser = argparse.ArgumentParser(
        prog='python -m annotate', description='Annotation project connecting the Chandra Data Archive and Source Catalog with ALeRCE')
    parser.add_argument('--a', metavar='ARCHIVE', type=str, default='CDA',
                        help='Workflow branch - CDA or CSC (default: %(default)s)')
    parser.add_argument('--c', metavar='CLASSIFER', type=str, default='lightcurve',
                        help='ZTF Classifier - stamp or lightcurve (default: %(default)s)')
    parser.add_argument('--d', metavar='DATE', type=str, help='Date of detection that ALerCE database is queried. Formatted as YYYY-MM-DD (default: Current date)',
                        default=datetime.today().strftime("%Y-%m-%d"))
    parser.add_argument('--n', metavar='NOVEL_OBJECTS', type=int,
                        help='Whether only newly detected objects are retrieved from ALeRCE - 1=True, 0=False (default: %(default)s)', default=1)

    return parser
