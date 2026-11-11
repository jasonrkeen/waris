"""Regenerate the reviewed illustrative gap table from the bundled numeric input."""
from pathlib import Path
import argparse
from review_methods import read,write,gap_projection
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Use a new output file; preserve prior artifacts')
    write(args.output,gap_projection(read(args.input)))
