#!/usr/bin/python

'''
HTTP query switchboard. Interprets request parameters and calls functions to handle request.
This could be replaced by a Python web framework such as Flask or Django if things got really complicated.
'''
import os
import sys
import json
import efsm_config as config
# TODO: the matplotlib stuff should be in another module
if config.hostdomain == 'unknown':
    os.environ['HOME'] = '/tmp/'    # required for matplotlib on local system, but not FNMOC sservers
import traceback
import logging
logger = logging.getLogger('efsm_query')

def mouse_to_geo(x,y):
    '''
    Convert mouse coordinates to lon-lat. This is especially difficult because it depends on the
    map projection. But if Matplotlib/Basemap can convert from lon-lat to display (pixel) coordinates,
    obviously there's a way back.
    :param x:
    :param y:
    :return: HTTP containing JSON with a variety of different XY coordinate pairs. Only lon-lat is needed.
    '''
    logger.debug('muose_to_geo: convert {0},{1} to geo coords'.format(x,y))
    import matplotlib
    matplotlib.use('Agg')
    from mpl_toolkits.basemap import Basemap
    import matplotlib.pyplot as plt
    from pylab import rcParams
    rcParams['figure.figsize'] = config.map_size
    fig = plt.gcf() # get current figure
    fig.set_dpi(config.map_dpi)

    bm = Basemap(projection='mill', resolution='c', lon_0=180)
    bm.drawcoastlines()  # must have this line, else transData will be Identity!
    fig.canvas.draw()  # absolutely must render NOW in order to get correct display/pixels coords!
    ax = fig.gca()  # get current axes

    newval = {'x_mouse':x,'y_mouse':y}
    inv = ax.transData.inverted()
    proj_xy = inv.transform((x,y))
    newval['x_proj'] = str(proj_xy[0])
    newval['y_proj'] = str(proj_xy[1])
    lon,lat = bm(proj_xy[0],proj_xy[1],inverse=True)
    newval['lon'] = lon
    newval['lat'] = lat
    inv = ax.transAxes.inverted()
    axes_xy = inv.transform((x,y))
    newval['x_ax'] = axes_xy[0]
    newval['y_ax'] = axes_xy[1]

    print 'Content-type: application/json\n'
    print json.dumps(newval)

def geo_to_disp(lon,lat):
    '''
    Convert geographic lon-lat coordinates to display coordinates (pixels).
    This is needed when user inputs lon-lat coordinates from text boxes, instead of just
    clicking on map with mouse.
    :param lon:
    :param lat:
    :return: HTTP containing JSON with a variety of different XY coordinate pairs. Only x_disp,y_disp is needed.
    '''
    import matplotlib
    matplotlib.use('Agg')
    from mpl_toolkits.basemap import Basemap
    import matplotlib.pyplot as plt
    from pylab import rcParams
    rcParams['figure.figsize'] = config.map_size
    fig = plt.gcf() # get current figure
    fig.set_dpi(config.map_dpi)

    bm = Basemap(projection='mill', resolution='c', lon_0=180)
    bm.drawcoastlines()  # must have this line, else transData will be Identity!
    fig.canvas.draw()  # absolutely must render NOW in order to get correct display/pixels coords!
    ax = fig.gca()  # get current axes

    logger.debug('geo_to_disp: %s,%s' %(lon,lat))
    newval = {'lon':str(lon),'lat':str(lat)}
    try:
        geo_xy  = (lon,lat)
        proj_xy = bm(float(lon),float(lat))
        #logger.debug('geo_to_disp: proj_xy=%s' %(str(proj_xy)))

        #proj_xy_s = xy_format.format(proj_xy[0],proj_xy[1])
        disp_xy = ax.transData.transform(proj_xy)
        #disp_xy_s = xy_format.format(disp_xy[0],disp_xy[1])
        inv = ax.transAxes.inverted()
        axes_xy = inv.transform(disp_xy)

        newval['x_disp'] = str(disp_xy[0])
        newval['y_disp'] = str(disp_xy[1])
        newval['x_ax'] = str(axes_xy[0])
        newval['y_ax'] = str(axes_xy[1])
        newval['x_proj'] = str(proj_xy[0])
        newval['y_proj'] = str(proj_xy[1])
    except Exception,ex:
        e = sys.exc_info()
        logger.error('ex0=%s' %(e[0]))
        logger.error('ex1=%s' %(e[1]))
        for line in traceback.extract_tb(e[2]):
            logger.error(line)

    print 'Content-type: application/json\n'
    print json.dumps(newval)

def clear_cache():
    '''
    Delete all cached image files from the app tmp directory.
    This is used for dev work, but could also be called by a cron job.
    :return: nothing
    '''
    from glob import glob
    dir = config.tmpDir
    #logger.debug('clear_cache: %s, %s' %(dir+'/*.png',str(glob(dir+'/*.png'))))
    for f in glob(dir+'/*.png'):
        os.remove(f)

if __name__ == '__main__':
    import cgi
    import cgitb
    cgitb.enable()

    cgiform = cgi.FieldStorage()
    logger.debug(str(cgiform))

    action = cgiform.getfirst('action')
    logger.debug('action=%s'%(action))
    if action == 'map_click':           # user clicked on map for plume plot
        # transofmr mouse coords to display coords and to geo coords
        x = cgiform.getfirst('x')
        y = cgiform.getfirst('y')
        mouse_to_geo(x,y)
    elif action == 'plume':         # user entered lon-lat in text box for plume plot
        lon = cgiform.getfirst('lon')
        lat = cgiform.getfirst('lat')
        geo_to_disp(lon,lat)
    elif action == 'plume_plot':    # webapp requests a plume plot image
        logger.debug('start plume_plot')
        modname = __import__('efsm_plume')
        modname.webcall(cgiform)
    elif action == 'clear_cache':   # clear cached image files
        clear_cache()
    elif action == 'contours':
        # Returns default contour values for the selected field
        retval = {}
        fld_lvl = cgiform.getfirst('fld_lvl')
        contours = config.get_contours(fld_lvl)
        retval['contours'] = contours
        logger.debug('fld_lvl=%s, contours=%s' %(fld_lvl,str(contours)))
        print 'Content-type: application/json\n'
        print json.dumps(retval)


#..................START EPILOGUE......................................
#
# CONFIGURATION IDENTIFICATION:  @(#)$Id$
#
# NAME:                          efsm_query.py
#
# AUTHOR:                        Glenn Nelson / Forward Slope
#
# DESCRIPTION:                   switchboard for HTTP queries. Interpret
#                                query and call handler functions
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

