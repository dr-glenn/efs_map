#!/usr/bin/python

'''
Generate plume plots by reading ensemble values at specific lon-lat for all tau values.
'''
import os
import os.path
import sys
import traceback
import efsm_config as config
import efsv_isis_fnmoc as isis
import copy
from string import Template
import cgi
import numpy as np
import logging
logger = logging.getLogger('efsm_plume')

'''
Create plume plots at a lat-long location
'''
cgi_app = False

class PlumeData:
    '''
    Gather data from all ensemble members, store in variable indexed as values[ens_index][tau]
    '''
    # TODO: need grid spacing as an arg so that we can do 720x361 and other global grids
    def __init__(self,lon,lat,dtg,field,lvl_type,level,**kwargs):
        '''
        Create the PlumeData class. The primary parameters are used to fetch grids from ISIS.
        :param lon: longitude
        :param lat: latitude
        :param dtg: 10 digit YYYYMMDDHH
        :param field: ISIS name of field
        :param lvl_type: 'surface', 'ht_sfc', 'isbr_lvl' are common
        :param level: integer value of level (we don't use ISIS level1, only use level0)
        :param kwargs: other ISIS args that we don't care about. model='ENSEMBLE', dset='fcst_et', etc.?
        :return: instance of PlumeData
        '''
        logger.debug('PlumeData: %s,%s,%s,%s,%s,%s'%(lon,lat,dtg,field,lvl_type,level))
        logger.debug('PlumeData: kwargs = %s' %(str(kwargs)))
        # TODO: how to use kwargs?
        for key in kwargs:
            setattr(self,key,kwargs[key])
        self.lonlat = (lon,lat)
        self.field = field
        self.dtg = dtg
        self.lvl_type = lvl_type
        self.level = level
        # TODO: uses default of 360x181, need more args here
        self.isis_params = isis.ISIS_GRID_PARAMS(dtg,field,tau=0,level_type=lvl_type,level0=float(level))
        self.taus = config.taus
        self.params = self._make_params()
        logger.debug('PlumeData attributes: %s'%(self.__dict__.keys()))

    def _make_params(self):
        '''
        private function: Create copies of ISIS_GRID_PARAMS for each member and tau. We need copies for each in order to fetch
        grids from ISIS.
        :return: dict of ISIS_GRID_PARAMS indexed by [ens_index][tau]
        '''
        params = {}
        for ens_num in range(1,config.n_ensem_members+1):
            params[ens_num] = {}
            for tau in self.taus:
                params[ens_num][tau] = copy.copy(self.isis_params)
                params[ens_num][tau].tau = float(tau)
        return params

    def gather_field(self):
        '''
        Gather field values at the specified lonlat.
        :param isis_params: ISIS_GRID_PARAMS object, will make clones
        :param taus: list of tau values, typically 0 to 240
        :param lonlat: (lon,lat) tuple
        :return: numpy array indexed by [ensemble number,tau]
        '''
        gather = {}
        # calc array index for plume point
        # TODO: this will never work for 720x361
        ilon = int(self.lonlat[0])
        ilat = int(self.lonlat[1] + 90.0)
        for ens in self.params:
            gather[ens] = {}
            for tau in self.params[ens]:
                p = self.params[ens][tau]   # fetch ISIS_GRID_PARAMS instance
                # TODO: instead of reading entire grid, make a method to read a single grid value
                igrid = isis.ISIS_GRID.iread(p,ens) # read entire grid
                if igrid.valid:
                    #igrid = np.reshape(igrid,p.gridsize,order='F')  # It should already be correct shape, so don't run this line.
                    #logger.debug('gather_field: igrid shape=%s' %str(igrid.shape))
                    # TODO: note that I have to reverse indices: (lat,long) instead of expected (long,lat)! Should fix this.
                    # Why? I reversed indices in ISIS_GRID.__new__. Why? I was forced to do that because the contour plots were not working out.
                    # Why? Because I used numpy.meshgrid to create x,y for contour plot and did not fully understand this function.
                    #logger.debug('ens=%d, tau=%d: val=%f' %(ens,tau,igrid[ilat,ilon]))
                    gather[ens][tau] = igrid[ilat,ilon]
                else:
                    logger.debug('gather_field: missing ens=%s, tau=%s' %(str(ens),str(tau)))
        return gather

def webcall(form=None):
    '''
    Entry point that is called by efsm_query when user action requests 'efsm_plume'
    :param form: CGI form, expected to have parameters for ISIS (field, DTG, etc.) and lon-lat of interest
    :return: nothing, but program will send results to HTTP stream
    '''
    global cgi_app
    global isis_params
    #logger.debug('form=%s' %(str(form)))
    cgi_app = True
    if config.hostdomain == 'unknown':
        os.environ['HOME'] = '/tmp/'
        #localhost = True
    import matplotlib
    matplotlib.use('Agg')
    lon = float(form.getfirst('lon'))
    lat = float(form.getfirst('lat'))
    dtg = form.getfirst('dtg')
    model = form.getfirst('model','ENSEMBLE')
    field = form.getfirst('field')
    lvl_type = form.getfirst('lvl_type','surface')
    level0 = float(form.getfirst('level0','0'))
    level1 = 0.0
    dset = form.getfirst('dset','fcst_et')
    tau = int(form.getfirst('tau','0'))
    grid = form.getfirst('grid','global_360x181')
    #myargs = {'lon':lon,'lat':lat,'dtg':dtg,'model':model,'field':field,'lvl_type':lvl_type,'level':level0,'dset':dset,'tau':tau,'grid':grid}
    myargs = {'lon':lon,'lat':lat,'dtg':dtg,'field':field,'lvl_type':lvl_type,'level':level0,'model':model}
    #logger.debug('webcall: call main')
    main(myargs)

def main(myargs):
    '''
    Generates plume plot as XY graph. x-axis is tau, y-axis is field value.
    :param myargs: see function 'webcall' above
    :return: nothing, but program will send plume plot figure to HTTP stream
    '''
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    from matplotlib import rcParams
    rcParams.update({'figure.autolayout': True})
    logger.debug('start main')
    try:
        # Example of creating PlumeData:
        #pp = PlumeData(180.0,-45.0,'2016022500','wnd_spd','isbr_lvl',850)
        pp = PlumeData(**myargs)
        plume = pp.gather_field()   # plume[ens_index][tau] is collectin of the values at lon-lat location
        logger.debug('number of plumes = %d' %(len(plume)))
        fig = plt.figure(figsize=(3,2))
        plt.gcf().subplots_adjust(left=0.18)
        for ens in plume:
            px = sorted(plume[ens])
            py = [plume[ens][x] for x in px]
            #logger.debug('ens = %s, y = %s' %(str(ens),str(py)))
            if len(py) > 0:     # we might be missing ensemble members
                plt.plot(px,py)
        ax = fig.gca()
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        if cgi_app == False:
            plt.show()
        else:
            #logger.debug('output plume img')
            print 'Content-Type: image/png\n'
            plt.savefig( sys.stdout, format='png' )
    except Exception,ex:
        e = sys.exc_info()
        logger.error('ex0=%s' %(e[0]))
        logger.error('ex1=%s' %(e[1]))
        for line in traceback.extract_tb(e[2]):
            logger.error(line)

if __name__ == '__main__':
    '''
    Called only if run from command line (and might not work)
    '''
    import matplotlib
    matplotlib.use('GTKAgg')
    myargs = {'lon':180.0,'lat':-45.0,'dtg':'2016022500','field':'wnd_spd','lvl_type':'isbr_lvl','level':850}
    main(myargs)


#..................START EPILOGUE......................................
#
# CONFIGURATION IDENTIFICATION:  @(#)$Id$
#
# NAME:                          efsm_plume.py
#
# AUTHOR:                        Glenn Nelson / Forward Slope
#
# DESCRIPTION:                   generate plume plots and send to web browser as PNG image
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

