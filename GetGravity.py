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
#   Script to grab graivty data from BeagleBone dataloggers

import argparse
import logging
import os
import shutil
import tomputils.util as tutil

from datetime import datetime, timedelta
from ftplib import FTP

# Args
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', type=str, required=True,
                    help='Config File')

# General
path = 'grav/{0}/{1}/{2}.dat'
tmpfile = '/tmp/{0}{1}{2}.dat'
lamp = '/lamp/valve3/def/gravity/raw'
archive = '/def/gravity/data/raw/{0}/{1}'
logfile = '/def/gravity/log/grav.log'


def load_config(conf):
    sites = {}
    logger.info('Parsing Config')
    with open(conf, 'r') as infile:
        for line in infile:
            logger.info(f'Adding station: {line.rstrip()}')
            split = line.split(',')
            sites[split[0]] = split[1]
    return sites


def convert_times(f, m):
    with open(f, 'r') as infile:
        with open(m, 'w') as outfile:
            for line in infile:
                split = line.split(',')
                idt = split[0]
                dtobj = datetime.strptime(idt, '%m-%d-%y %H:%M:%S.%f')
                y, m, d, H, M, S = dtobj.timetuple()[:6]
                ms = timedelta(microseconds=round(dtobj.microsecond / 1000.0)
                               * 1000.0)
                ms_date = datetime(y, m, d, H, M, S) + ms
                split[0] = ms_date.strftime('%m-%d-%y %H:%M:%S.%f')[:-3]
                outfile.write(', '.join(split))


def datalogger_to_valve_and_archive(sites):
    year = datetime.utcnow().year
    day = datetime.utcnow().timetuple().tm_yday
    hour = datetime.utcnow().hour - 1
    if hour < 0:
        if day > 1:
            day = day - 1
        else:
            day = (datetime.strptime("%s/12/31" % year - 1, "%Y/%m/%d")
                           .timetuple().tm_yday)
        hour = 23
    day = str(day).zfill(3)
    hour = str(hour).zfill(2)
    logger.info(f'Grabbing data for year: {year}, day: {day}, hour: {hour}')
    remotefile = path.format(year, day, hour)
    archiveloc = archive.format(year, day)
    for key, val in sites.items():
        localfile = tmpfile.format(key, day, hour)
        logger.info(f'Getting file ({remotefile}) for station: {key}')
        try:
            # Retrieve the file
            ftp = FTP(val)
            ftp.login()
            ftp.retrbinary('RETR %s' % remotefile, open(localfile, 'wb').write)
            ftp.quit()

            # Copy it to the local archive
            if not os.path.exists(archiveloc):
                os.mkdir(archiveloc)
            logger.info(f'Copying to {archiveloc}')
            shutil.copy2(localfile, archiveloc)

            # Now parse local file, moving from microseconds to milliseconds
            # Then copy to the lamp directory
            modfile = f'{localfile[:-4]}mod.dat'
            convert_times(localfile, modfile)
            logger.info(f'Copying to {lamp}\n')
            shutil.copy2(modfile, lamp)
            os.remove(modfile)
            os.remove(localfile)
        except Exception as e:
            logger.error(e)


if __name__ == '__main__':
    global logger
    logger = tutil.setup_logging("GetGravity")
    if 'PYLOGLEVEL' in os.environ:
        level = logging.getLevelName(os.getenv('PYLOGLEVEL', 'DEBUG'))
        logger.setLevel(level)

    logger.info('Starting')
    args = parser.parse_args()
    sites = load_config(args.config)
    datalogger_to_valve_and_archive(sites)
    logger.info('Finished')
    logging.shutdown()
