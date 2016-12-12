# Stub file for use by efsv_isis_fnmoc.py.
# On non-FNMOC system, it provides functions to read/write ISIS files in a local directory without
# actually using FNMOC ISIS.
# On FNMOC systems, we compile f2py_isis.f90 and do not deploy this module.
# The functions have the same interface, whether python or fortran.

import efsm_config as config

# OK, this looks dangerous - circular imports! But it actually should be OK.
import efsv_isis_fnmoc as isis
#from efsv_isis_fnmoc import ISIS_GRID_PARAMS
import numpy as np

def iread(dtg, which_model, geometry, nx, ny, \
          field_name, units, tau, \
          lvl_name, in_lvl1, in_lvl2, \
          isis_dset, ens_num):
    '''
    This function reads ISIS files direct from disk - it does not use ISIS API.
    Input params are the values needed by ISIS read function.
    return: 1-D grid or None if file not found
    '''
    '''
    if ens_num == 0:
        dset = isis_dset
    else:
        dset = '{0}{1:03d}'.format(isis_dset,ens_num)
    '''
    geom = 'global_{0:d}x{1:d}'.format(nx,ny)
    gridsize = (nx,ny)
    iparams = isis.ISIS_GRID_PARAMS(dtg,field_name,which_model,tau,units,lvl_name,in_lvl1,in_lvl2,gridsize,isis_dset)

    # This is test code to replace f2py_isis.so, so we will read ISIS files directly from a known directory.
    grid = None
    filename = iparams.genFilename(ens_num)
    if config.hostdomain == 'unknown':
        infile = '../data/{0}/{1}'.format(dtg,filename)
    else:
        # assume we're on a FNMOC server and have ISIS
        infile = '/isis/ops/grid/ENSEMBLE/{0}/{1}'.format(dtg,filename)
    try:
        fd = open(infile, "rb")
    except IOError:
        grid = None
    else:
        # read the 512 byte ISIS header
        header = np.fromfile(fd, dtype='<f', count=128)
        grid = np.fromfile(file=fd, dtype='<f')   # little-Endian 4 byte float
        #grid = np.reshape(grid,gridsize,order='F')
    return grid

def iwrt(dtg,which_model,field_name, \
        units, tau, lvl_name, in_lvl1, in_lvl2, \
        isis_dset, ens_num, \
        ens_field):
    '''
    :param dtg:
    :param which_model:
    :param field_name:
    :param units:
    :param tau:
    :param lvl_name:
    :param in_lvl1:
    :param in_lvl2:
    :param isis_dset:
    :param ens_num:
    :param ens_field: ISIS_GRID object, numpy 2D array, nx=longitude, ny=latitude
    :return:
    '''
    #geom = 'global_{0:d}x{1:d}'.format(nx,ny)
    gridsize = ens_field.shape()
    #iparams = isis.ISIS_GRID_PARAMS(dtg,field_name,which_model,tau,units,lvl_name,in_lvl1,in_lvl2,gridsize,isis_dset)
    #ens_field.iwrite(ens_num)
    return
