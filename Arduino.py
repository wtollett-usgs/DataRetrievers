#!/usr/bin/env python
#
# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode
#
# Author(s):
#   Bill Tollett <wtollett@usgs.gov>
#
# Description:
#   Script to grab data from HVORest/HVOLib Arduino devices and output
#   results for Cacti ingestion.

import requests
import sys


def main(args):
    try:
        host = f'http://{args[0]}'
        r = requests.get(f'{host}/all_sensors')
        data = r.json()
        data.pop('name')
        return ' '.join([f'{k}:{v:.2f}' for k, v in data.items()])
    except Exception:
        # Something went wrong -- return a blank line.
        return ''


if __name__ == '__main__':
    output = main(sys.argv[1:])
    print(output)
