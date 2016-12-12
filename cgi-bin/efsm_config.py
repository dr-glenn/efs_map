#!/usr/bin/env python

# This file is included in all other python in this app. It defines some constants used by the application
# and sets up application logging.

import os
# logging is used to write ERROR, WARNING, INFO and sometimes DEBUG messages.
# The messages are written to roatating log files in the app logs directory.
import logging
import logging.handlers

hostdomain = 'unknown'
wwwRoot = '/var/www/html'  # common desktop Linux will use this
wxmapRootURL = '/wxmap_cgi/#ensemble'   # used to link to FNMOC WxMap pages

hostname = os.uname()[1]    # fetch hostname from 'os' services
localhost  = True   # not FNMOC, will use local data samples
if (hostname.find('fnmoc.navy.mil') >= 0 or hostname.find('web4') >= 0):
    hostdomain = 'fnmoc.navy.mil'
    wwwRoot = '/opt/global/webservices/apache/app'
    localhost = False

# Application root in Apache
appRoot = '/efs_map'

tmpDir = wwwRoot+appRoot+'/dynamic/tmp'     # cache for PNG files (maps)

# CSS and Javascript libs
# Load libs for FNMOC servers. web4 is FNMOC public server.
if hostname.find('fnmoc.navy.mil') >= 0 or hostname.find('web4') >= 0:
    commonRoot = '/common/'
    # CSS for FNMOC Portal
    fnmocCSS = commonRoot+'css/'+'viz_stds.css'
else:
    # Paths for local dev system
    commonRoot = '/common/'
    # CSS for FNMOC Portal
    fnmocCSS = appRoot+'/css/'+'viz_stds.css'

# Spinning wheel for busy indicator
jqueryBusyLib = appRoot+'/js/'+'jquery.busy.min.js'

# Setup standard rotating log files, esp. handy for debug info.
log_dir   = '../log/'       # relative to where CGI is deployed
LOG_FILENAME = log_dir + 'efsm.log'
#logging.basicConfig(filename=LOG_FILENAME, format='%(asctime)s %(name)s %(levelname)s %(message)s')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
# max length of log file is 4 MB, keep 4 previous files
fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=4000000, backupCount=4)
fileHandler.setFormatter(formatter)
# use of rootLogger: by modifying unnamed logger here, we are setting level and handler
# defaults that will be inherited by all other loggers in this suite.
# GDN: this approach is better than changing logging.basicConfig, but I don't remember why.
rootLogger = logging.getLogger('')
# setLevel here determines the level that gets passed to this handler.
# There can be other handlers with different rules.
fileHandler.setLevel(logging.DEBUG)
# setLevel here determines the level that will be handled by root logger
rootLogger.setLevel(logging.DEBUG)
rootLogger.addHandler(fileHandler)

bUseOL3 = True
if bUseOL3:
    map_size = (8,4)    # matplotlib figure size in inches - good aspect ration for global maps
else:
    map_size = (8, 6)  # matplotlib figure size in inches - good aspect ration for global maps
map_dpi  = 200.0    # pixels per inch, it doesn't need to match monitor

taus = range(0,241,24)  # from 0 to 240 hours, step 24
n_ensem_members = 20    # number ensemble members in ISIS
n_ensem_display = 20    # number ensemble members to be displayed in spaghetti maps

# Known fields
# Match ISIS field name and level value to obtain the ISIS level type.
# These 3 parameters are required when calling ISIS to retrieve grid.
isis_field = [
    # (ISIS field name, level value, ISIS level type)
    ('wnd_spd',     '850',  'isbr_lvl'),
    ('wnd_spd',     '250',  'isbr_lvl'),
    ('wnd_spd',     '10',   'ht_sfc'),
    ('air_temp',    '2',    'ht_sfc'),
    ('ttl_prcp_06', '0',    'surface'),
]
# index field short name to ISIS field name and field title)
field_lookup = {
    'wnd':  ('wnd_spd',     'Wind Speed'),
    'temp': ('air_temp',    'Air Temp'),
    'prcp': ('ttl_prcp_06', 'Total Precip 06')
}
# Fields and their breakpoints for spaghetti plots
spag_vals = {
    ('wnd_spd',850): (20.0, 27.0, 34.0),
    ('wnd_spd',250): (40.0, 60.0, 80.0),
    ('wnd_spd',10):  (5.0, 10.0, 20.0),
    ('air_temp',2):  (263.15, 273.15, 283.15),
    ('ttl_prcp_06',0): (5.0, 10.0, 20.0),
}

def get_contours(fld_lvl):
    '''
    Return the contour (spaghetti) values for the chosen field and level
    :param fld_lvl: combination of both field type and level value
    :return: list or tuple of float values
    '''
    fld,lvl = fld_lvl.split('_')
    fld1 = field_lookup[fld][0]     # get the ISIS name
    key = (fld1,int(lvl))
    return spag_vals[key]

#..................START EPILOGUE......................................
#
# CONFIGURATION IDENTIFICATION:  @(#)$Id$
#
# NAME:                          efsm_config.py
#
# AUTHOR:                        Glenn Nelson / Forward Slope
#
# DESCRIPTION:                   application global constants and setup
#
# CONTRACT NUMBER AND TITLE:     n/a
#
# REFERENCES:                    none
#
# CLASSIFICATION:                unclassified
#
# RESTRICTIONS:                  Python 2.6+
#
# FPATH:                         none
#
# USAGE:                         none (file is imported by other Python)
#
#...................END EPILOGUE........................................

