#!/usr/bin/env python3
"""MAKEIMAGE local demo; creates actual PNG and provenance JSON."""
import argparse
from src.makeimage_flow import render

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', help='Optional source image; requires --licensed-source')
    p.add_argument('--licensed-source', action='store_true', help='Confirm source rights')
    p.add_argument('--output', default='output/makeimage-demo.png')
    p.add_argument('--title', default='MAKEIMAGE')
    p.add_argument('--subtitle', default='Visuals with proof, not invented claims.')
    args = p.parse_args()
    image, receipt = render(args.output, source=args.input,
                            licensed_source=args.licensed_source,
                            title=args.title, subtitle=args.subtitle)
    print(f'Rendered {image}; proof {receipt}; not approved for publication')

if __name__ == '__main__':
    main()
