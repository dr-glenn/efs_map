#
'''
Read and write ISIS files at FNMOC.
This is a module that you will import to your Python program.
It includes grid manipulation functions that perform some simple arithmetic on grids.
When run standalone it executes a short test.
'''

'''
GDN Notes, 10 July 2015:
I've been able to subclass np.ndarray. But now I don't know how to properly
use ISIS_GRID.read. The ISIS_GRID class already has an array of zeros.
When I call read, I want the grid to replace the ISIS_GRID instance, but
only the array contents, not the rest of the instance.

OTOH, the ISIS_GRID.write method seems to be correct.

Maybe the read method should actually return a new instance of ISIS_GRID?
Or read method should be a classmethod?

Other note: gridsize=(360,181). If ndarray is created with shape=gridsize,
then everything works out OK. 
But the read method does this:
    mygrid = np.zeros((ny,nx),np.float32,'F')
So I think that this must be equivalent to:
    mygrid = np.zeros((nx,ny),np.float32)
'''
__version__ = '$Rev: 43270 $'

import efsm_config as config
import logging
logger = logging.getLogger('efsv_isis_fnmoc')
import copy
import numpy as np
import datetime
import re
import f2py_isis as isis

ISIS_INVALID = 1.0e10

# Create list of files or parameters that we need to fetch from ISIS
taus = range(0,241,12)
iensem = range(1,21)
model = 'ENSEMBLE'
nx = 360
ny = 181
field = 'ttl_prcp'
tau   = '12'
#dtg10 = '2015062600'

class FLAT_GRID_PARAMS:
    '''
    All the parameters necessary to uniquely identify a flat grid.
    An instance of this class will be contained in a FLAT_GRID object.
    '''
    def __init__(self, filename, dtg='', field='', model='ENSEMBLE', tau=0, units='?', \
                 level_type='surface', level0=0.0, level1=0.0, \
                 gridsize=(360,181), dset='fcst_et'):
        self.filename = filename
        self.dtg = dtg
        self.nx = gridsize[0]
        self.ny = gridsize[1]

class FLAT_GRID(np.ndarray):
    '''
    Stores a header-less grid file.
    '''
    def __new__(cls, input_array, \
                grid_params=None, header=None):
        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = np.asarray(input_array).view(cls)
        obj[ obj == ISIS_INVALID ] = np.nan     # change ISIS_INVALID to numpy NaN
        # add the new attributes to the created instance
        obj.params = grid_params
        obj.header = header
        # Finally, we must return the newly created object:
        return obj

    # This would be constructor when you want to create a new, empty array.
    def newnew(subtype, shape, dtype=float, buffer=None, offset=0, \
                strides=None, order=None, info=None, \
                grid_params=None, header=None):
        # Create the ndarray instance of our type, given the usual
        # ndarray input arguments.  This will call the standard
        # ndarray constructor, but return an object of our type.
        # It also triggers a call to InfoArray.__array_finalize__
        obj = np.ndarray.__new__(subtype, shape, dtype, buffer, offset, strides, order)

        # set the new attributes to the values passed
        obj.params = grid_params
        obj.header = header
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # ``self`` is a new object resulting from
        # ndarray.__new__(InfoArray, ...), therefore it only has
        # attributes that the ndarray.__new__ constructor gave it -
        # i.e. those of a standard ndarray.
        #
        # We could have got to the ndarray.__new__ call in 3 ways:
        # From an explicit constructor - e.g. InfoArray():
        #    obj is None
        #    (we're in the middle of the InfoArray.__new__
        #    constructor, and self.info will be set when we return to
        #    InfoArray.__new__)
        if obj is None: return
        # From view casting - e.g arr.view(InfoArray):
        #    obj is arr
        #    (type(obj) can be InfoArray)
        # From new-from-template - e.g infoarr[:3]
        #    type(obj) is InfoArray
        #
        # Note that it is here, rather than in the __new__ method,
        # that we set the default value for 'params', because this
        # method sees all creation of default objects - with the
        # InfoArray.__new__ constructor, but also with
        # arr.view(InfoArray).
        self.params = getattr(obj, 'params', None)
        self.header = getattr(obj, 'header', None)
        # We do not need to return anything

    '''
    def __eq__(self, other):
        if isinstance(other, FLAT_GRID):
            # TODO: how to compare 2 ISIS_GRID objects?
            # np.array_equal(a1,a2)
            return False
        elif isinstance(other, float):
            # TODO: how to compare with a float array?
            return False
        else:
            return False    # not implemented
    '''

    @classmethod
    def fread(cls,filename,gridsize=(360,181)):
        '''
        Read a "flat-file", create FLAT_GRID object.
        :param filename: probably NRL-style name, but could be anything
        :param gridsize: default is 360x181. It must match what is in the file.
        :return: a FLAT_GRID instance
        '''
        print 'fread: filename=%s'%(str(filename))
        mygrid = np.zeros(gridsize[1],gridsize[0],np.float32,'F')
        # get data from ISIS via fortran routine.  NB i_ensm==0 returns deterministic
        fd = open(filename, 'rb')
        (mygrid) = np.fromfile(file=fd, dtype='<f')   # little-Endian 4 byte float
        print 'len(mygrid) = %d' %len(mygrid)
        print 'reshape: %s' %str((prm.ny,prm.nx))
        (mygrid) = np.reshape(mygrid,(prm.ny,prm.nx))
        print 'after fread: shape = %s' %(str(mygrid.shape))
        #return np.swapaxes(mygrid,0,1)  # from ISIS it's nx,ny but we want ny,nx so swap
        prm = FLAT_GRID_PARAMS(filename,gridsize=gridsize)
        return FLAT_GRID(mygrid, grid_params=prm)

    @classmethod
    def pread(cls,prm):
        '''
        Read a "flat-file", create FLAT_GRID object.
        :param prm: FLAT_GRID_PARAM object that must contain a valid filename
        :return: a FLAT_GRID instance
        '''
        print 'prm: %s' %str(prm)
        mygrid = np.zeros((prm.ny,prm.nx),np.float32,'F')
        # get data from ISIS via fortran routine.  NB i_ensm==0 returns deterministic
        fd = open(prm.filename, "rb")
        (mygrid) = np.fromfile(file=fd, dtype='<f')   # little-Endian 4 byte float
        print 'len(mygrid) = %d' %len(mygrid)
        print 'reshape: %s' %str((prm.ny,prm.nx))
        (mygrid) = np.reshape(mygrid,(prm.ny,prm.nx))
        #print 'after fread: %f, shape = %s' %(mygrid[100,100],str(mygrid.shape))
        print 'after fread: shape = %s' %(str(mygrid.shape))
        #return np.swapaxes(mygrid,0,1)  # from ISIS it's nx,ny but we want ny,nx so swap
        return FLAT_GRID(mygrid, grid_params=prm)

    def write(self,filename=None):
        '''
        Writes a flat grid.
        :param filename: optional and may include a path. If not specified,
                         then use filename from self.params.
        :return: nothing
        '''
        prm = self.params
        if filename:
            prm.filename = filename
        if False:
            self.astype('float32').tofile(prm.filename)
        else:
            # Ugh, must convert NaN back to ISIS_INVALID
            #fd = open(prm.filename, "wb")
            outarr = self
            outarr[np.isnan(outarr)] = ISIS_INVALID
            outarr.astype('float32').tofile(prm.filename)

class ISIS_GRID_PARAMS:
    '''
    All the parameters necessary to uniquely identify an ISIS grid.
    '''
    def __init__(self, dtg, field, model='ENSEMBLE', tau=0, units='?', \
                 level_type='surface', level0=0.0, level1=0.0, \
                 gridsize=(360,181), dset='fcst_et'):
        '''
        :param dtg: no default, 10 digit character string (YYYYMMDDHH)
        :param field: no default, ISIS field name
        :param model: default='ENSEMBLE'
        :param tau: default=0, value is in hours. Can be string or int.
        :param units: default='?'. ISIS chooses default for each field name. Override if you want to change units.
        :param level_type: default='surface'. Other values are 'isbr_lvl', 'ht_sfc' and more.
        :param level0: default=0.0. When level_type!='surface', then levels are usually in millibars or meters.
        :param level1: default=0.0. When level_type!='surface', then levels are usually in millibars or meters.
        :param gridsize: default=(360,181). Two element tuple. Only other expected value is (720,361).
        :param dset: default='fcst_et', for ensemble members. Some other values are 'fcst_ops', 'fcst_bc'.

        NOTE: can only be used to fetch global grids, not regional.
        '''
        self.model = model
        self.dtg = dtg
        self.tau = float(tau)
        self.field = field
        self.units = units
        self.level_type = level_type
        self.level0 = float(level0)
        self.level1 = float(level1)
        self.gridsize = gridsize
        self.nx = gridsize[0]
        self.ny = gridsize[1]
        self.geometry = 'global_%03dx%03d' %(gridsize[0],gridsize[1])
        self.dset = dset
        if False:
            logger.debug('ISIS_GRID_PARAMS:')
            logger.debug('model=%s'%(model))
            logger.debug('dtg=%s'%(dtg))
            logger.debug('tau=%d'%(tau))
            logger.debug('field=%s'%(field))
            logger.debug('units=%s'%(units))
            logger.debug('level_type=%s'%(level_type))
            logger.debug('level0=%f'%(level0))
            logger.debug('level1=%f'%(level1))
            logger.debug('gridsize=%s'%(str(gridsize)))
            logger.debug('dset=%s'%(str(dset)))
            logger.debug('ISIS_GRID_PARAMS: done')

    @classmethod
    def parseFilename(cls,isis_filename):
        '''
        Parse the ISIS filename to get all the params needed for ISIS call.
        :param isis_filename: Usually a name with colon char to separate the fields
        :return: ISIS_GRID_PARAMS object
        '''
        # Example: ENSEMBLE:2016012500:global_360x181:wnd_spd:isbr_lvl:08500000:00000000:fcst_et007:1440
        params = isis_filename.split(':')
        # TODO: can I do without assumptions in next few lines?
        grid_dim = params[2][len('global_'):]
        gridsize = [int(d) for d in grid_dim.split('x')]
        if re.search('\d\d\d$',params[7]):
            dset = params[7][:-3]
        else:
            dset = params[7]    # assumed to be not ensemble type
        level0 = float(params[5][:4])   # ignore last 4 zeroes
        level1 = float(params[6][:4])
        return ISIS_GRID_PARAMS(dtg=params[1],field=params[3],model=params[0],tau=params[8],
                                units='?',level_type=params[4],level0=params[5],level1=params[6],
                                gridsize=gridsize,dset=dset)

    def genFilename(self,ensem_num=0):
        '''
        Generate ISIS filename based on parameters in ISIS_GRID_PARAMS
        :param ensem_num: if==0, assume non-ensemble and simply use dset in filename.
                          if!=0, append 3-digit value to dset, e.g., fcst_et005
        :return: filename
        '''
        # Example: ENSEMBLE:2016012500:global_360x181:wnd_spd:isbr_lvl:08500000:00000000:fcst_et007:1440
        dset = self.dset
        if ensem_num != 0:
            dset += '%03d' %(ensem_num)
        gridsize = 'global_%dx%d' %(self.nx,self.ny)
        level0 = '{0:04.0f}0000'.format(self.level0)
        level1 = '{0:04.0f}0000'.format(self.level1)
        filename = '%s:%s:%s:%s:%s:%s:%s:%s:%03d0' %(self.model,self.dtg,gridsize,self.field,
                                self.level_type,level0,level1,
                                dset,int(self.tau))
        return filename


# In order to subclass from np.ndarray, you should use __new__ and not __init__.
# And there's more ... read this: http://docs.scipy.org/doc/numpy/user/basics.subclassing.html
class ISIS_GRID(np.ndarray):
    def __new__(cls, input_array, \
                grid_params, header=None):
        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        if input_array is None:
            obj = np.zeros((grid_params.ny,grid_params.nx),dtype='<f').view(cls)
            #obj = np.zeros((grid_params.nx,grid_params.ny),dtype='<f').view(cls)
            obj.valid = False
        else:
            new_arr = np.reshape(input_array,(grid_params.ny,grid_params.nx),order='C')
            #new_arr = np.reshape(input_array,(grid_params.nx,grid_params.ny),order='F')
            obj = np.asarray(new_arr).view(cls)
            obj[ obj == ISIS_INVALID ] = np.nan     # change ISIS_INVALID to numpy NaN
            obj.valid = True
        # add the new attributes to the created instance
        obj.params = copy.copy(grid_params)
        if header:
            obj.header = copy.copy(header)
        else:
            obj.header = None
        # Finally, we must return the newly created object:
        return obj

    # This would be constructor when you want to create a new, empty array.
    def newnew(subtype, shape, dtype=float, buffer=None, offset=0, \
                strides=None, order=None, info=None, \
                grid_params=None, header=None):
        # Create the ndarray instance of our type, given the usual
        # ndarray input arguments.  This will call the standard
        # ndarray constructor, but return an object of our type.
        # It also triggers a call to InfoArray.__array_finalize__
        obj = np.ndarray.__new__(subtype, shape, dtype, buffer, offset, strides, order)

        # set the new attributes to the values passed
        obj.params = grid_params
        obj.header = header
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # ``self`` is a new object resulting from
        # ndarray.__new__(InfoArray, ...), therefore it only has
        # attributes that the ndarray.__new__ constructor gave it -
        # i.e. those of a standard ndarray.
        #
        # We could have got to the ndarray.__new__ call in 3 ways:
        # From an explicit constructor - e.g. InfoArray():
        #    obj is None
        #    (we're in the middle of the InfoArray.__new__
        #    constructor, and self.info will be set when we return to
        #    InfoArray.__new__)
        if obj is None: return
        # From view casting - e.g arr.view(InfoArray):
        #    obj is arr
        #    (type(obj) can be InfoArray)
        # From new-from-template - e.g infoarr[:3]
        #    type(obj) is InfoArray
        #
        # Note that it is here, rather than in the __new__ method,
        # that we set the default value for 'params', because this
        # method sees all creation of default objects - with the
        # InfoArray.__new__ constructor, but also with
        # arr.view(InfoArray).
        #obj[ obj == ISIS_INVALID ] = np.nan     # change ISIS_INVALID to numpy NaN
        self.params = getattr(obj, 'params', None)
        self.header = getattr(obj, 'header', None)
        # We do not need to return anything

    # TODO: may not need to override __eq__ because ISIS_GRID is an instance of ndarray
    #       When we create ISIS_GRID, we make sure that all ISIS_INVALID values are first
    #       converted to NaN, so we should be able to use default __eq__
    '''
    def __eq__(self, other):
        if isinstance(other, ISIS_GRID):
            # TODO: how to compare 2 ISIS_GRID objects?
            return np.array_equal(self,other)
        elif isinstance(other, float):
            # TODO: how to compare with a float array?
            return False
        else:
            return False    # not implemented
    '''

    @classmethod
    def iread(cls,prm,i_ensm):
        '''
        Read an ISIS grid, create ISIS_GRID object.
        :param prm: ISIS_GRID_PARAMS object
        :param i_ensm: ensemble member number. Typically a value from 1 to 20.
        :return: an ISIS_GRID instance, with 2-D,32-bit numpy float array
        NOTE: uses f2py_isis.so to invoke FNMOC ISIS library.
        '''
        #mygrid = np.zeros((prm.ny,prm.nx),np.float32,'F')
        # TODO: should copy prm here and not in __init__
        # get data from ISIS via fortran routine.  NB i_ensm==0 returns deterministic
        # f2py_isis.py will return a 1-D array, but mygrid is (ny,nx)
        mygrid = isis.iread(prm.dtg, prm.model, prm.geometry, prm.nx, prm.ny, \
                              prm.field, prm.units, prm.tau, \
                              prm.level_type, prm.level0, prm.level1, \
                              prm.dset, i_ensm)
        #print 'after iread: %f, shape = %s' %(mygrid[100,100],str(mygrid.shape))
        #return np.swapaxes(mygrid,0,1)  # from ISIS it's nx,ny but we want ny,nx so swap
        return ISIS_GRID(mygrid, prm)

    # TODO: this method not used, maybe shouldn't exist
    def read(self,i_ensm):
        '''
        Read an ISIS grid, return ISIS_GRID object.
        :param i_ensm: ensemble member number. Typically a value from 1 to 20.
        :return: an ISIS_GRID instance, with 32-bit numpy float array

        NOTE: uses f2py_isis.so to invoke FNMOC ISIS library.
        NOTE1: maybe not needed to return the grid, since this is an instance method.
        '''
        mygrid = np.zeros((prm.ny,prm.nx),np.float32,'F')
        prm = self.params
        mygrid = np.zeros((ny,nx),np.float32,'F')
        # get data from ISIS via fortran routine.  NB i_ensm==0 returns deterministic
        (mygrid) = isis.iread(prm.dtg, prm.model, prm.geometry, prm.nx, prm.ny, \
                              prm.field, prm.units, prm.tau, \
                              prm.level_type, prm.level0, prm.level1, \
                              prm.dset, i_ensm)
        #print 'after read: %f, shape = %s' %(mygrid[100,100],str(mygrid.shape))
        #return np.swapaxes(mygrid,0,1)  # from ISIS it's nx,ny but we want ny,nx so swap
        return mygrid

    def iwrite(self,i_ensm):
        '''
        Writes a grid to ISIS DB. If you don't have permission (and you probably don't),
        then it will write to I2E_GRID_WRITE, which you need to specify in the shell script
        that invokes this python program.
        :param i_ensm: ensemble member number. Typically a value from 1 to 20.

        NOTE: uses f2py_isis.so to invoke FNMOC ISIS library.
        '''
        prm = self.params

        if False:
            print 'write_field_isis: args'
            print '  shape  = %s' %str(self.arr.shape)
            print '  dtg    = %s' %(prm.dtg)
            print '  tau    = %f' %(float(prm.tau))
            print '  model  = %s' %(prm.model)
            print '  field  = %s' %(prm.field)
            print '  nx,ny  = %d,%d' %(prm.nx,prm.ny)
            print '  dset   = %s' %(prm.dset)
            print '  i_ensm = %d' %(i_ensm)
        outarr = self
        outarr[np.isnan(outarr)] = ISIS_INVALID
        (ierr) = isis.iwrt(prm.dtg, prm.model, \
                           prm.field, prm.units, float(prm.tau), \
                           prm.level_type, prm.level0, prm.level1, \
                           prm.dset, i_ensm, outarr )
        return ierr

    def max_arrs(self, *others):
        '''
        Return ndarray that contains max value at each point of the multiple inputs.
        '''
        print 'max_arrs: field = %s' %(self.params.field)
        maxarr = self  # may not need copy if len(others)==1
        for isis_arr in others:
            print 'max_arrs: field = %s' %(isis_arr.params.field)
            maxarr = np.maximum(maxarr,isis_arr)
        return maxarr

    def avg_arrs(self, *others):
        '''
        return ndarray that is element-wise average of all input arrays
        '''
        avgarr = self  # may not need copy if len(others)==1
        for isis_arr in others:
            avgarr = np.add(maxarr,isis_arr)
        return avgarr / (1 + len(others))

def computeOffsetDTG( timeDTG, days=0, hours=0 ):
    '''
    Return the DTG at which model was run. (timeDTG - leadTime)
    Args:
    timeDTG - 10 digit string: year, month, day, hour - probably DTG of XML file
    days - default=0, in days, plus or minus.
    hours - default=0, in hours, plus or minus.
    '''
    compDTG = datetime.datetime( int(timeDTG[0:4]), int(timeDTG[4:6]), int(timeDTG[6:8]), int(timeDTG[8:10]) )
    # timedelta( days, seconds, microseconds ) - requires seconds and microseconds to be positive
    if hours >= 0:
        secs = hours * 3600
    else:
        # hours are converted to seconds and must be positive, so let's fix it up
        # e.g., if hours=-30, then we need to subtract 2 days from day value and add (48-30) to hours.
        hours = -hours
        hour_days = int(hours / 24) + 1
        hour_hours = 24 - (hours % 24)

        days = days - hour_days
        secs = hour_hours * 3600

    tdiff = datetime.timedelta( days=days, seconds=secs )
    # expected time when last analysis was completed
    tempDTG = compDTG + tdiff
    #logger.debug('computeOffsetDTG: %s, %s'%(str(compDTG),str(tempDTG)))
    return '%04d%02d%02d%02d' %(tempDTG.year, tempDTG.month, tempDTG.day, tempDTG.hour)

# def test_add2():
#     global nx, ny
#     global model, field, dtg10, tau
#     tau0 = tau
#     tau1 = tau
#     dtg0 = dtg10
#     dset = 'fcst_et'
#     level_type = 'surface'
#     level0 = level1 = 0.0
#     units = 'kg/m**2'
#     dtg1 = computeOffsetDTG(dtg10,days=0, hours=-12)
#
#     gridsize = (360,181)
#     # grid_params: dtg0 is current DTG, dtg1=dtg0-12 hours
#     grid_params0 = ISIS_GRID_PARAMS(dtg0,field,model,tau,units,level_type,level0,level1,gridsize=(360,181),dset=dset)
#     grid_params1 = ISIS_GRID_PARAMS(dtg1,field,model,tau,units,level_type,level0,level1,gridsize=(360,181),dset=dset)
#
#     # read using class method and create new instance of ISIS_GRID
#     # Must give the ensemble number as second arg
#     iensm = 1
#     igrid0 = ISIS_GRID.iread(grid_params0,iensm)
#     igrid1 = ISIS_GRID.iread(grid_params1,iensm)
#     gridsum1 = igrid0 + igrid1  # look, we can use numpy directly!
#     print 'igrid0 class = %s' %(type(igrid0).__name__)
#     print 'gridsum1 class = %s' %(type(gridsum1).__name__)
#     print 'after add grids: %f, %s' %(gridsum1[100,100],str(gridsum1.shape))
#
#     # The output is a 24 hour period, so change field name (hope it's allowed by ISIS)
#     field = 'prcp_25_2'   # 24 hour precip by summing two 12 hour intervals (need local copy of ISIS grid_parm.dat)
#     gridsum1.params.field = field
#     gridsum1.iwrite(iensm)

# TODO: test_flat is really not useful yet, because it requires the full filename,
#       instead of constructing it from parameters.
# TODO: probably should make a flat_write method for ISIS_GRID.
def test_flat():
    global nx, ny
    global model, field, dtg10, tau
    tau0 = tau
    tau1 = tau
    dtg0 = dtg10
    dset = 'fcst_et'
    level_type = 'surface'
    level0 = level1 = 0.0
    units = 'kg/m**2'
    dtg1 = computeOffsetDTG(dtg10,days=0, hours=-12)

    fname1 = 'totpcp_sfc_0000.0_0000.0_glob360x181_2015090612_00120000_fcstfld'
    fname2 = 'totpcp_sfc_0000.0_0000.0_glob360x181_2015090700_00120000_fcstfld'
    gridsize = (360,181)
    grid_params0 = FLAT_GRID_PARAMS(fname1,dtg0)
    grid_params1 = FLAT_GRID_PARAMS(fname1,dtg1)
    print 'grid_params0: %s, nx=%d, ny=%d' %(grid_params0.filename,grid_params0.nx,grid_params0.ny)

    # read using class method and create new instance of ISIS_GRID
    # Must give the ensemble number as second arg
    iensm = 1
    igrid0 = FLAT_GRID.pread(grid_params0)
    igrid1 = FLAT_GRID.pread(grid_params1)
    gridsum1 = igrid0 + igrid1  # look, we can use numpy directly!
    print 'igrid0 class = %s' %(type(igrid0).__name__)
    print 'gridsum1 class = %s' %(type(gridsum1).__name__)
    print 'after add grids: %f, %s' %(gridsum1[100,100],str(gridsum1.shape))

    # The output is a 24 hour period, so change field name (hope it's allowed by ISIS)
    field = 'ttl_prcp_24'   # may need local copy of ISIS grid_parm.dat if using 'ttl_prcp_24'
    gridsum1.params.filename = 'flat.grd'
    gridsum1.iwrite()

def create_prcp_24(dtg10, model='ENSEMBLE', dset='fcst_et', field='ttl_prcp', \
                   tau1=240, tau_interval=24, interval=6, gridsize=(360,181)):
    '''
    Create 24 hour precip files by adding four 6 hour precip files.
    Generate 24 hour cumulative grids for tau=range(0,240,24).
    Our precip forecasts are denoted by end time, not start time, thus tau=6 is cumulative precip ending 6 hours from dtg10.
    Thus our cumulative files are like this: tau=48 will be sum of ttl_prcp_06 forecasts at 30, 36, 42 and 48 hours.
    :param dtg10: 10 digit YYYYMMDDHH as a string
    :param model: ENSEMBLE is FNMOC NAVGEM. Other possibilities are CMC_ENSEMBLE and NCEP_ENSEMBLE
    :param dset: 'fcst_et' gets raw ensemble members. 'fcst_bc' gets bias-corrected members.
                 'fcst_ops' gets deterministic grids, model must be 'UKMET' or 'NAVGEM'.
    :param field: 'ttl_prcp' is the root for either 06 or 12 hour cumulative
    :param interval: duration of the forecast inputs (6 or 12 hours)
    :param gridsize: can also handle (720,361), but no other dimensions are supported
    '''
    # TODO: interval and tau increment should be used to calculate number of grids to sum
    # TODO: should check model and dset are compatible
    if dset == 'fcst_ops':
        n_ensem = 1
    else:
        n_ensem = 20
    if model == 'UKMET':
        field = 'ttl_prcp'  # sure wish they appended num of hours to their field name
    else:
        field = '%s_%02d' %(field,interval)     # field names are ttl_prcp_06 or ttl_prcp_12
    level_type = 'surface'
    level0 = level1 = 0.0
    units = 'kg/m**2'
    #tau_interval = 24
    taus = range(0,tau1+1,tau_interval)
    ngrid = tau_interval / interval
    print 'ngrid=%d' %(ngrid)
    for tau in taus:
        dtg = []
        grid_params = []
        if tau == 0:
            if ngrid == 4:
                # funny stuff because there shouldn't be a precip tau=0 forecast, but we need it
                dtg.append(computeOffsetDTG(dtg10,days=0, hours=-24))   # six hour grid from -24 hours
                dtg.append(computeOffsetDTG(dtg10,days=0, hours=-24))   # six hour grid from -24 hours
                dtg.append(computeOffsetDTG(dtg10,days=0, hours=-12))   # six hour grid from -12 hours
                dtg.append(computeOffsetDTG(dtg10,days=0, hours=-12))   # six hour grid from -12 hours
                # ISIS_GRID_PARAMS contain all parameters required to read/write from FNMOC ISIS
                # First two grids are 6 hour cumulative from 6 hours and at 12 hours from 24 hours back
                grid_params.append(ISIS_GRID_PARAMS(dtg[0],field,model,tau+interval,units,level_type,level0,level1,gridsize=(360,181),dset=dset))
                grid_params.append(ISIS_GRID_PARAMS(dtg[1],field,model,tau+2*interval,units,level_type,level0,level1,gridsize=(360,181),dset=dset))
                # Next two grids are 6 hour accumulation at 6 hours and at 12 hours from 12 hours back
                grid_params.append(ISIS_GRID_PARAMS(dtg[2],field,model,tau+interval,units,level_type,level0,level1,gridsize=(360,181),dset=dset))
                grid_params.append(ISIS_GRID_PARAMS(dtg[3],field,model,tau+2*interval,units,level_type,level0,level1,gridsize=(360,181),dset=dset))
            elif ngrid == 2:
                # funny stuff because there shouldn't be a precip tau=0 forecast, but we need it
                dtg.append(computeOffsetDTG(dtg10,days=0, hours=-24))   # twelve hour grid from -24 hours
                dtg.append(computeOffsetDTG(dtg10,days=0, hours=-12))   # twelve hour grid from -12 hours
                # ISIS_GRID_PARAMS contain all parameters required to read/write from FNMOC ISIS
                # First grid is 12 hour cumulative from 24 hours back
                grid_params.append(ISIS_GRID_PARAMS(dtg[0],field,model,tau+interval,units,level_type,level0,level1,gridsize=(360,181),dset=dset))
                # Second grid is 12 hour cumulative from 12 hours back
                grid_params.append(ISIS_GRID_PARAMS(dtg[1],field,model,tau+interval,units,level_type,level0,level1,gridsize=(360,181),dset=dset))
            #print str(dtg)
        else:    # tau != 0
            dtg = [dtg10 for n in range(0,ngrid)]
            # ISIS_GRID_PARAMS contain all parameters required to read/write from FNMOC ISIS
            # All 4 grids are 6 hour accumulation for current DTG, starting with tau and advancing by 6, 12, 18
            # For example, if tau=48, then we want to add the 6 hr forecasts for 30, 36, 42, 48
            for i,d in enumerate(dtg):
                grid_params.append(ISIS_GRID_PARAMS(d,field,model,(tau-24)+(i+1)*interval,units,level_type,level0,level1,gridsize=(360,181),dset=dset))
#
        # read using class method and create new instance of ISIS_GRID
        # Must give the ensemble number as second arg
        for iensm in range(1,n_ensem+1):
            igrid = []
            for gp in grid_params:
                print 'tau=%d, iensm=%d, gp.field=%s' %(int(tau),iensm,gp.field)
                igrid.append(ISIS_GRID.iread(gp,iensm if n_ensem > 1 else 0))
            gridsum1 = igrid[0]
            print 'max=%.2f' %(np.max(gridsum1))
            for grd in igrid[1:]:
                gridsum1 += grd     # look, we can use numpy directly to add entire grids!
                print 'max sum=%.2f' %(np.max(gridsum1))
#
            # The output is a 24 hour period, so change field name (hope it's allowed by ISIS)
            field_out = 'prcp_24_%d' %(ngrid)   # 24 hour precip by summing ngrid files (need local copy of ISIS grid_parm.dat)
            field_out = 'prcp_24'  # 24 hour precip by summing ngrid files (need local copy of ISIS grid_parm.dat)
            gridsum1.params.field = field_out
            gridsum1.params.tau   = float(tau)
            gridsum1.params.dtg   = dtg10    # because for tau=0, the dtg value is (incorrectly) yesterday
            print 'gridsum: dtg=%s, tau=%f' %(gridsum1.params.dtg, gridsum1.params.tau)
            gridsum1.iwrite(iensm if n_ensem > 1 else 0)   # iensm==0 for 'fcst_ops'
#
            # Now try to write fcst_ops file to ENSEMBLE subdir
            if n_ensem <= 1:
                #gridsum1.params.field = field_out
                #gridsum1.params.tau   = float(tau)
                #gridsum1.params.dtg   = dtg10    # because for tau=0, the dtg value is (incorrectly) yesterday
                gridsum1.params.model  = 'ENSEMBLE'
                gridsum1.iwrite(iensm if n_ensem > 1 else 0)   # iensm==0 for 'fcst_ops'
    
def main(argv):
    # Get ensemble forecast grids
    # Loop over tau: 0 to 240
    # Fetch current DTG files
    # Fetch previous DTG files
    # Add files to make 24 hour precip
    # Write to ALT_ISIS
    global model, field, dtg10, tau
    try:
        opts,args = getopt.getopt(argv, "m:f:d:t:", ["model=","field=","dtg=","tau="])
        for opt,arg in opts:
            if opt in ('-m','--model'):
                model = arg
            elif opt in ('-f','--field'):
                field = arg
            elif opt in ('-d','--dtg'):
                dtg10 = arg
            elif opt in ('-t','--tau'):
                tau = arg
    except getopt.GetOptError:
        print "Error: you didn't run with correct args"
        usage()
        sys.exit(2)
#
    print 'Args: %s, %s, %s, %s' %(model,field,dtg10,tau)
    create_prcp_24(dtg10, model=model, interval=12)
    #test_add2()
    #test_flat()
    '''
    print 'dtg10=%s' %(dtg10)
    days = 0
    hours = 12
    d = computeOffsetDTG(dtg10,days=days,hours=hours)
    print 'days=%d, hours=%d, date=%s' %(days,hours,d)
    days = 0
    hours = -24
    d = computeOffsetDTG(dtg10,days=days,hours=hours)
    print 'days=%d, hours=%d, date=%s' %(days,hours,d)
    days = -1
    hours = 0
    d = computeOffsetDTG(dtg10,days=days,hours=hours)
    print 'days=%d, hours=%d, date=%s' %(days,hours,d)
    '''
#
def usage():
    print 'isis_fnmoc <--dtg VAL> [--model VAL] [--field VAL] [--tau VAL]'
#
if __name__ == '__main__':
    import os
    import sys
    import getopt
    print 'argv: %s' %str(sys.argv)
    main(sys.argv[1:])

#..................START EPILOGUE......................................
#
# CONFIGURATION IDENTIFICATION:  $Id: efsv_isis_fnmoc.py 43270 2016-05-19 20:39:06Z glenn.d.nelson $
#
# AUTHOR:                        Glenn Nelson / Forward Slope
#
# DESCRIPTION:                   interface to FNMOC ISIS, uses official ISIS API to read AND write ISIS grids
#
# CONTRACT NUMBER AND TITLE:     n/a
#
# REFERENCES:                    none
#
# CLASSIFICATION:                unclassified
#
# RESTRICTIONS:                  Python 2.6 or later. Fortran f2py compiler required.
#
# FPATH:                         none
#
# USAGE:                         none (file is imported by other Python)
#
#...................END EPILOGUE........................................
