#!/usr/bin/python

'''
Code to handle img src URL.
Web page <img src=efsm_img.py?<form values>> will invoke this script, which then
calls efsm_isis to generate image.
'''

# TODO: why not just make this the main() entry in efsm_isis?

import os
import sys
import cgi
import cgitb
cgitb.enable()
import efsm_config as config
import logging
logger = logging.getLogger('efsm_img')
import traceback

form = cgi.FieldStorage()
logger.debug('form='+str(form))
#logger.debug('map=%s' %(form.getfirst('map')))

if form.getfirst('map') == 'spaghetti':
    try:
        modname = __import__('efsm_isis')
        modname.webcall(form)
    except:
        e = sys.exc_info()
        logger.error('ex0=%s' %(e[0]))
        logger.error('ex1=%s' %(e[1]))
        for line in traceback.extract_tb(e[2]):
            logger.error(line)
else:
    logger.warning('do not have valid "map" value')

