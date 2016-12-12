#!/usr/bin/env python

'''read ISIS grid files, display with color contour lines'''

# spaghetti plot. Choose 3 values for wind or whatever field. Each value gets a unique color.
# Plot contours for all ensemble members.

# Example filename from ISIS:
# ENSEMBLE:2015123000:global_360x181:wnd_spd:isbr_lvl:08500000:00000000:fcst_et001:0240

'''
NOTES:
- How to handle user settable contour values.
Contour values are displayed in GUI.
Checkbox enables user to override default values.
  If checkbox is off, then values should be fetched from server and will be default values.
  If checkbox is on, then values are whatever is in the number text boxes.
Contour image files must have contour values in the filename.
Javascript must know the currently selected contour values in order to create hidden img filenames.
We can use session cookie to store user overrides, but ultimately must use identity.

'''

import os
import sys
import cgi      # for reading parameters from HTTP URL
import resource
from datetime import datetime
import numpy as np
import re       # regular expression parser
import efsm_config as config
import logging  # see efsm_config.py for more info about logger
logger = logging.getLogger('efsm_isis')
import traceback    # for debugging disasters
import efsv_isis_fnmoc as isis  # read ISIS files, convert to object ISIS_GRID

cgi_app = False     # default assumes run from command line (which is actually unlikely)

isis_params = None

''' log_time is used as a function decorator: for timing individual functions'''
# Decorators are easy to use but very difficult to explain!
# When you use log_time decorator in front of another function 'func', then the total runtime
# of 'func' will be recorded in the app logs.
import time
def log_time(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        logger.debug('%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0))
        return res
    return wrapper

def allFiles(infile):
    '''
    Parse infile (ISIS filename), return a list of the ISIS names of all the ensemble files.
    :param infile: ISIS filename for one ensemble member
    :return: list of ISIS filenames for all ensemble members (including infile)
    '''
    fparse = infile.split(':')
    logger.debug( str(fparse) )
    ens_str = fparse[-2]
    logger.debug( 'ens_str: %s'%(ens_str) )
    fnames = []
    #for ens in range(1,config.n_ensem_members+1):
    for ens in range(1,config.n_ensem_members+1,(config.n_ensem_members/config.n_ensem_display)):
        fnames.append(re.sub('fcst_et...','fcst_et%03d'%(ens),infile))
    return fnames

contours = []
def webcall(form=None):
    '''
    Entry when used in web page.
    :param form: All CGI form parameters
    :return:
    '''
    global cgi_app      # True if called from web page, False if run from command line
    global isis_params
    global contours
    logger.debug('form=%s' %(str(form)))
    cgi_app = True
    if config.hostdomain == 'unknown':
        os.environ['HOME'] = '/tmp/'    # matplotlib uses this dir. FNMOC servers already define it.
    import matplotlib
    #matplotlib.use('GTKAgg')
    #matplotlib.use('TKAgg')
    matplotlib.use('Agg')       # backend that is used for web graphics
    if not form:
        form = cgi.FieldStorage()
    # Get the values from HTTP URL parameters:
    dtg = form.getfirst('dtg')
    model = form.getfirst('model','ENSEMBLE')   # default to ENSEMBLE if 'model' not declared
    field = form.getfirst('field')
    lvl_type = form.getfirst('lvl_type','surface')  # default to 'surface' if 'lvl_type' not declared
    level0 = float(form.getfirst('level0','0'))
    level1 = 0.0
    dset = form.getfirst('dset','fcst_et')
    tau = int(form.getfirst('tau','0'))
    grid = form.getfirst('grid','global_360x181')   # this is expected ISIS designation of grid dimensions
    grid_dim = grid[len('global_'):]
    gridsize = [int(d) for d in grid_dim.split('x')]    # will be tuple (360,181) or maybe (720,361)
    contours = form.getlist('contour[]')
    if len(contours) > 0:
        contours = [int(cval) for cval in contours]
    logger.debug('webcall: create ISIS_GRID_PARAMS')
    # Create object that holds all params required by ISIS API to fetch a grid:
    isis_params = isis.ISIS_GRID_PARAMS(dtg=dtg,field=field,model=model,tau=tau,level_type=lvl_type,level0=level0,gridsize=gridsize,dset=dset)
    filename = isis_params.genFilename(1)   # ISIS filename for ensemble member = 1
    if config.localhost:
        # full ISIS file path on local system
        filename = '../data/{0}/{1}'.format(dtg,filename)
    else:
        # assume we're on a FNMOC server and have ISIS
        # full ISIS file path on FNMOC
        filename = '/isis/ops/grid/ENSEMBLE/{0}/{1}'.format(dtg,filename)
    # TODO: should pass isis_params and not filename
    # TODO: should make it work so that we really do use ISIS and not just read files directly
    logger.debug('webcall: filename=%s'%(filename))
    # TODO: should call main with cgi form args
    main(['web',filename])

def httpSendCache(cacheFile):
    '''
    Map image files are cached by app. If the cacheFile exists, output to HTTP stream and return True.
    If cacheFile does not exist, simply return False.
    :param cacheFile: test for existence of cacheFile and output to HTTP
    :return: True if cache found, False otherwise
    '''
    if os.path.exists(cacheFile):
        logger.debug('output http: cache: %s' %(cacheFile))
        print 'Content-Type: image/png'
        # Output of "Content-Length" header is optional, but if not used, then Apache will
        # not send output until Python CGI completely exits. When "Content-Length" is present,
        # Apache will send output as soon as its buffer is filled.
        fstat = os.stat(cacheFile)
        print 'Content-Length: '+str(fstat.st_size)
        print ''    # extra newline required to terminate HTTP header block
        # TODO: maybe should also send Expires header?
        infile = open( cacheFile, 'rb' )
        while True:
            data = infile.read(4096)    # buffered read
            if not data:
                break   # no more input
            # TODO - when changed to Python 3.x, I believe this statement needs to be
            #    changed to sys.stdout.buffer.write(data) and maybe even wrap with
            #    UTF-8 encoder.
            sys.stdout.write(data)
        infile.close()
        # flush stdout - shouldn't be needed, but screen draw seems slow.
        sys.stdout.flush()
        return True
    else:
        return False

@log_time
def main(argv):
    '''
    main does all the plotting
    '''
    from mpl_toolkits.basemap import Basemap
    import matplotlib.pyplot as plt
    from matplotlib import rcParams
    rcParams['figure.figsize'] = config.map_size
    #plt.figure(figsize=config.map_size)    # this method to set figsize might not always work
    fig = plt.gcf() # get current figure - the entire plotting area
    # TODO: not sure why these next 3 lines are here - I think I only wanted them for command line debugging
    fig.set_frameon(True)
    fig.patch.set_visible(True)
    fig.patch.set_facecolor('green')  # just want to know what part of display is "figure"

    fig.set_dpi(config.map_dpi)
    global isis_params
    global cgi_app
    global contours
    upper_limit = 1.0e8
    bSetmax = False
    lower_limit = 1.0e8
    bSetmin = False
    hasHeader = True
    # TODO: gridx, gridy should not be fixed here
    gridx = 360
    gridy = 181
    
    ######### Parse command line args ###########
    # there are better ways to parse args, but this will do for this simple program
    if len(argv) > 1:
        iarg = 1
        while iarg < len(argv):
            arg = argv[iarg]
            if arg[0] == '-':
                if arg == '-max':
                    bSetmax = True
                    iarg += 1
                    upper_limit = float(argv[iarg])
                elif arg == '-min':
                    bSetmin = True
                    iarg += 1
                    lower_limit = float(argv[iarg])
                elif arg == '-gridx':
                    iarg += 1
                    gridx = int(argv[iarg])
            else:
                infiles = argv[iarg:]
                break
            iarg += 1
        gridy = gridx/2 + 1     # program only works for global grid
        grid_incr = 1.0/float(gridx/360)
    else:
        print 'requires ISIS filename on command line'
        sys.exit(1)
    
    # TODO: do something here to possibly display multiple panels if more than one infiles
    files = allFiles(infiles[0])    # from single filename, generate list of all enesmeble member files
    logger.debug( str(files) )
    
    # TODO: this code not needed for spaghetti, but we could do multi-panel display for different tau
    n_per_page = 4
    n_pages = (len(infiles)-1)/n_per_page + 1    # allow 4 per page
    if len(infiles) == 1:
        n_subplot = 1    # one file only will get entire plot area
        n_rows = 1
        n_cols = 1
    elif len(infiles) == 2:
        n_subplot = 2    # two files are displayed as one row, two columns
        n_rows = 1
        n_cols = 2
    else:
        n_subplot = n_per_page    # if 3 or more, then put 4 on a page
        n_rows = 2
        n_cols = 2

    # if all graphs should be same range
    zbreaks = None
    # TODO: next is setup of zbreaks for a filled contour - we don't use that
    if bSetmax and bSetmin:
        # Since user set min/max, we set the Z for contourf plots with 8 colors.
        zrange = upper_limit - lower_limit
        zint = zrange / 8.0
        zbreaks = [lower_limit+(zint*iz) for iz in range(0,9)]
    else:
        if len(contours) > 0:
            zbreaks = contours
            logger.debug('zbreaks=%s' %(str(zbreaks)))
        else:
            fld_id = (isis_params.field,isis_params.level0)
            if fld_id in config.spag_vals:
                zbreaks = config.spag_vals[fld_id]
            else:
                logger.error('fld_id = %s is not valid' %(str(fld_id)))
                zbreaks = (2,4,6)
    # 10m winds: 5,10,20
    # 2m air temp: -10,0,10
    zcolors = ('red','green','blue')     # too garish
    zcolors = ('maroon','seagreen','steelblue')   # steelblue is too dark
    zcolors = ('maroon','seagreen','lightskyblue')
    logger.debug('zbreaks=%s' %(str(zbreaks)))

    ######### Open grid file and plot it ###########
    iplot = 0    # current plot number, used to flag initial setup
    
    mpl99 = False       # special code may be needed for maplotlib version 0.99

    for infile in files:
        if not os.path.exists(infile):
            logger.warning('file not found: %s' %(infile))
            continue
        logger.debug('main: file=%s' %(infile))
        # Get field name to put into map title
        file_fields = infile.split(':')
        fld_title = file_fields[3]
        ####################################################################################
        # Read the map grid and sanitize it by setting max and NaN values to something sane
        try:
            logger.debug('call ISIS_GRID.iread: %d' %(iplot+1))
            map_data = isis.ISIS_GRID.iread(isis_params,iplot+1)
            logger.debug('return from ISIS_GRID.iread')
            valid_data = map_data.valid
            dtg = isis_params.dtg
            tau = isis_params.tau
            level = isis_params.level0
            fld_title = isis_params.field
        except:
            valid_data = False
            e = sys.exc_info()
            logger.error('ex0=%s' %(e[0]))
            logger.error('ex1=%s' %(e[1]))
            for line in traceback.extract_tb(e[2]):
                logger.error(line)
        finally:
            pass

        if not valid_data:
            continue        # bad file, skip to next

        # Unique PNG filename for caching
        str_contours = '%d' %(int(zbreaks[0]))
        for z in zbreaks[1:]:
            str_contours += '-%d' %(int(z))
        img_name = '%s_%s_%.1f_%03d_%s.png' %(isis_params.dtg,fld_title,level,tau,str_contours)
        cacheFile = '%s/%s' %(config.tmpDir,img_name)
        if cgi_app:
            # TODO: httpSendCache should call plotting function if cacheFile does not exist
            status = httpSendCache(cacheFile)
            if status:
                return  # image found in cache and already sent to HTTP

        # If we get here, then the image was not found in cache
        # TODO: remaing code in main() should be a separate function and should be called by httpSendCache
        if iplot == 0:
            # Setting up plot figure first time through
            # my_axes is a numpy array (n_rows x n_cols) - neat!
            logger.debug('plotit: setup plot')
            plt.close('all')
            try:
                # squeeze=False guarantees that returned object 'my_axes' is always a 2-D numpy array.
                # When squeeze=True (default), it will return a 2-D array only if nrows>1 and ncols>1.
                # TODO: spaghetti not expected to have subplots
                # NOTE: subplots not valid for mpl 0.99
                fig,my_axes = plt.subplots(nrows=n_rows, ncols=n_cols, squeeze=False)
                #plt.subplots_adjust(bottom=0.10,left=0.10)
            except:
                pass
            if True:    # instead of using subplots functionality, just pretend this is mpl 0.99 and do it the old-fashioned way
                # old matplotlib 0.99 does not have method "subplots"
                mpl99 = True
                fig = None
                #my_axes = np.array((n_rows,n_cols))
                #my_axes = np.array(dtype=object,ndmin=2)
                # TODO: should make my_axes into a numpy 2-D array, but how?
                my_axes = []
                for r in range(n_rows):
                    my_axes.append([])
                    for c in range(n_cols):
                        my_axes[r].append(plt.subplot(n_rows,n_cols,(c+1)+(r*n_cols)))
                    
        nmax = 0
        nmin = 0
        num_nan = 0
    
        try:
            # TODO: convert degree K to F
            #map_data = (9.0/5.0)*(map_data - 273.15) + 32.0
            # set upper_limit on the grid
            maxval = np.nanmax(map_data)
            minval = np.nanmin(map_data)
            # Count the NaN values and establish min and max for grid
            logger.debug('shape(map_data)=%s' %str(map_data.shape))
            # TODO: There are numpy methods that could eliminate the loop here
            for i in range(map_data.shape[0]):
                for j in range(map_data.shape[1]):
                    if np.isnan(map_data[i,j]):
                        num_nan += 1
                    if bSetmax:
                        # if user specified upper_limit, then set values greater than limit
                        # to a value greater than upper_limit.
                        # And if value is NaN, set it to an even larger value so we can see
                        # it easily on the map.
                        if map_data[i,j] > upper_limit:
                            map_data[i,j] = upper_limit * 1.2
                            nmax += 1
                        elif np.isnan(map_data[i,j]):
                            map_data[i,j] = upper_limit * 1.5
                    if bSetmin:
                        # if user specified lower_limit, then set values less than limit
                        # to a value less than lower_limit.
                        if map_data[i,j] < lower_limit:
                            # TODO: need a better way to alter map_data at lower_limit
                            map_data[i,j] = lower_limit - 1.0
                            nmin += 1
            #print len(map_data)
            if not bSetmax:
                upper_limit = maxval
            if not bSetmin:
                lower_limit = minval
            logger.debug('main: finished create map_data: valid=%s' %str(map_data.valid))
            logger.debug('-- min=%f, max=%f, num_nan=%d' %(minval,maxval,num_nan))
        except:
            e = sys.exc_info()
            logger.error('ex0=%s' %(e[0]))
            logger.error('ex1=%s' %(e[1]))
            for line in traceback.extract_tb(e[2]):
                logger.error(line)

        ####################################################################################
        # Plot the map_data
    
        try:
            # Which subplot?
            if False:
                # code for multi-panel display
                irow = iplot / n_cols
                icol = iplot % n_cols
            else:
                irow = icol = 0
            #print 'iplot=%d, irow=%d, icol=%d' %(iplot,irow,icol)
            #print 'my_axes len=%d' %(len(my_axes))
            if mpl99 == False:
                sub_axis = my_axes[irow,icol]
            else:
                sub_axis = my_axes[irow][icol]
                plt.subplot(n_rows,n_cols,(icol+1)+(irow*n_cols)) # make sure to select current subplot
            # TODO: next section should be only done once, but what if multiplot display?
            if iplot == 0:
                map_ax = Basemap(ax=sub_axis, projection='mill', resolution='c', lon_0=180)
                # plotting grid data on top of basemap
                lats0 = np.arange(-90.0,90.1,grid_incr)
                lons0 = np.arange(0.0,359.9,grid_incr)
                lons,lats = np.meshgrid(lons0, lats0)   # create 2D grid of all (lon,lat) points
                #print '%d,%d' %(len(lons),len(lats))
                x,y = map_ax(lons, lats)    # convert (lon,lat) to x,y - projection coordinates
                logger.debug('contour shapes: map_data=%s, x=%s, y=%s' %(str(map_data.shape),str(x.shape),str(y.shape)))
            if zbreaks:
                cs = sub_axis.contour(x,y,map_data,levels=zbreaks,colors=zcolors)
                #cb = plt.colorbar(cs, shrink=0.8, extend='both')
            else:
                cs = sub_axis.contourf(x,y,map_data)

            '''
            # Get the actual contours so that we can use them somewhere else
            output = cs.collections.pop()
            paths = output.get_paths()[i] # for the various contours

            # the x,y coordinates can then be accessed as
            xcoords = paths.vertices.transpose()[0]
            ycoords = paths.vertices.transpose()[1]
            '''

            if iplot == 0:
                # plot coastlines, draw label meridians and parallels.
                map_ax.drawcoastlines()
                map_ax.drawparallels(np.arange(-90,90,30),labels=[1,0,0,0])
                #map_ax.drawmeridians(np.arange(map_ax.lonmin,map_ax.lonmax+30,60),labels=[0,0,0,1])
                map_ax.drawmeridians(np.arange(lons0[0],lons0[-1]+30,60),labels=[0,0,0,1])
                # fill continents 'coral' (with zorder=0), color wet areas 'aqua'
                map_ax.drawmapboundary(fill_color='grey')
                #map_ax.fillcontinents(color='coral',lake_color='aqua')
                #plt.colorbar(cs,ax=sub_axis,shrink=0.8)
                #plt.clabel(cs, inline=1, fontsize=10)
                labels = ['%.1f' %(z) for z in zbreaks]
                for i in range(len(labels)):
                    cs.collections[i].set_label(labels[i])
                plt.legend()

                #sub_axis.set_title('%s, level=%.1f, tau=%03d, dtg=%s\nmin/max = %g/%g\nnum < %g : %d, num > %g : %d, NaN: %d' \
                #                   %(fld_title,level,tau,dtg,minval,maxval,lower_limit,nmin,upper_limit,nmax,num_nan))
                sub_axis.set_title('%s, level=%.1f, tau=%03d, dtg=%s\nmin/max = %g/%g' \
                                   %(fld_title,level,tau,dtg,minval,maxval))

        except:
            e = sys.exc_info()
            logger.error('ex0=%s' %(e[0]))
            logger.error('ex1=%s' %(e[1]))
            for line in traceback.extract_tb(e[2]):
                logger.error(line)
        iplot += 1
        logger.debug('iplot=%d: memory use=%d'%(iplot,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        # TODO: multi-panel maps
        if False and iplot == n_per_page:
            iplot = 0
            #plt.tight_layout(pad=0.4)
            plt.show()
            for irow in range(n_rows):
                for icol in range(n_cols):
                    if mpl99 == False:
                        my_axes[irow,icol].cla()
                    else:
                        my_axes[irow][icol].cla()
            #plt.cla()
    
    if iplot > 0:
        if cgi_app:
            # Send map to HTTP stream
            logger.debug('write cache: %s' %(cacheFile))
            if not os.path.exists(cacheFile):
                plt.savefig(cacheFile, format='png', dpi=config.map_dpi)
                #plt.savefig(cacheFile+'.svg', format='svg')
                httpSendCache(cacheFile)
        else:
            # Show map in command line viewer
            logger.debug('output show')
            #plt.tight_layout(pad=0.4)
            plt.show()
    if False:
        # TODO: this is debug code only and it's been throwing exception
        # coordinate of center of map
        xy_fig = (0.5,0.5)
        logger.debug('xy_fig=%s' %(str(xy_fig)))
        xy_disp = F.transFigure.transform(xy_fig)
        logger.debug('xy_disp=%s' %(str(xy_disp)))
        # Convert display coordinates to data coordinates
        inv = sub_axis.transData.inverted()
        xy_data = inv.transform(xy_disp)
        logger.debug('1. xy_data=%s' %(str(xy_data)))
        xy_data = map_ax(xy_data[0],xy_data[1],inverse=True)
        logger.debug('2. xy_data=%s' %(str(xy_data)))

if __name__ == '__main__':
    '''
    If run from command line, we are just testing and will get a GTK window for display.
    argv is expected to be a filename. We need to break it apart, so that it seems like it
    was called from web.
    When run from cmd line, be sure to give full path to data file. Also you cannot run from
    web server dir because it attempts to write to log files that are owned by apache.
    So for cmd line testing you should run from dirs that you own.
    '''
    import matplotlib
    matplotlib.use('GTKAgg')
    #matplotlib.use('TKAgg')
    #matplotlib.use('Agg')
    main(sys.argv)


#..................START EPILOGUE......................................
#
# CONFIGURATION IDENTIFICATION:  @(#)$Id$
#
# NAME:                          efsm_isis.py
#
# AUTHOR:                        Glenn Nelson / Forward Slope
#
# DESCRIPTION:                   generate ensemble spaghetti maps as PNG files
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
