import sys
import argparse

def args_setup():
    parser = argparse.ArgumentParser(prog='python -m annotate', description='Annotation project connecting the Chandra Data Archive and Source Catalog with ALeRCE')
    parser.add_argument('--a', metavar='ARCHIVE', type=str, default='CDA', help='Workflow branch - CDA or CSC (default: %(default)s)')
    parser.add_argument('--c', metavar='CLASSIFER',type=str, default='lightcurve', help='ZTF Classifier - stamp or lightcurve (default: %(default)s)')
    parser.add_argument('--d', metavar='DAYS_AGO',type=float, help='Amount of days ago the ALerCE database is queried (default: %(default)s)', default=2.0)
    parser.add_argument('--n', metavar='NOVEL_OBJECTS',type=int, help='Whether only newly detected objects are retrieved from ALeRCE - 1=True, 0=False (default: %(default)s)', default=1)

    return parser
