import sys
import argparse
from . import program
from .args import args_setup

parser = args_setup()
pargs = parser.parse_args()
kwargs = {"archive": pargs.a, "classifier": pargs.c, "date": pargs.d, "novel_objects": bool(pargs.n)}

program.run(**kwargs)
