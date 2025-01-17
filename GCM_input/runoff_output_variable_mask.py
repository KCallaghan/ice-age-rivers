# Before running this, update "ocean_model_grid" with all land--ocean masks

# Arguments:
# 1. GRASS GIS location
# 2. Starting mask number (inclusive)
# 3. ending mask number (exclusive)
# 4. Starting time step (to avoid busy sqlite database error) --> doesn't matter

#from grass import script as grass
from Scientific.IO.NetCDF import NetCDFFile
import numpy as np
import shutil
import os
import sys
import subprocess
import glob
import sys

# specify (existing) location and mapset
#location = "G12_NA"
gisdb    = "/data4/grassdata"
location = str(sys.argv[1])
#location = "ICE6G_globalNoAnt"
#location = "ICE6G_Antarctica"
mapset   = "PERMANENT"
#gisdb    = "/media/awickert/data4/grassdata"

print ""
print location

nstart = None
nend = None
try:
  nstart = int(sys.argv[2])
  print "Starting at", nstart
except:
  pass
try:
  nend = int(sys.argv[3])
  print "Ending at (but exclusive of)", nend
except:
  pass
if nstart is nend:
  if nstart is None:
    print "Running for whole time-series"
print ""

try:
  sts = int(sys.argv[4])
except:
  sts = 0

# Can also get location internally:
# locname = grass.parse_command('g.gisenv', flags='s')['LOCATION_NAME'][1:-2]

# path to the GRASS GIS launch script
# MS Windows
grass7bin_win = r'C:\OSGeo4W\bin\grass71svn.bat'
# uncomment when using standalone WinGRASS installer
# grass7bin_win = r'C:\Program Files (x86)\GRASS GIS 7.0.0beta3\grass70.bat'
# Linux
grass7bin_lin = 'grass71'
# Mac OS X
# this is TODO
grass7bin_mac = '/Applications/GRASS/GRASS-7.1.app/'
 
# DATA
# define GRASS DATABASE
# add your path to grassdata (GRASS GIS database) directory
#gisdb = os.path.join(os.path.expanduser("~"), "grassdata")
# the following path is the default path on MS Windows
# gisdb = os.path.join(os.path.expanduser("~"), "Documents/grassdata") 
 
########### SOFTWARE
if sys.platform.startswith('linux'):
    # we assume that the GRASS GIS start script is available and in the PATH
    # query GRASS 7 itself for its GISBASE
    grass7bin = grass7bin_lin
elif sys.platform.startswith('win'):
    grass7bin = grass7bin_win
else:
    raise OSError('Platform not configured.')
 
# query GRASS 7 itself for its GISBASE
startcmd = [grass7bin, '--config', 'path']
 
p = subprocess.Popen(startcmd, shell=False,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate()
if p.returncode != 0:
    print >>sys.stderr, "ERROR: Cannot find GRASS GIS 7 start script (%s)" % startcmd
    sys.exit(-1)
gisbase = out.strip('\n\r')
 
# Set GISBASE environment variable
os.environ['GISBASE'] = gisbase
# the following not needed with trunk
os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')
# add path to GRASS addons
home = os.path.expanduser("~")
os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')
 
# define GRASS-Python environment
gpydir = os.path.join(gisbase, "etc", "python")
sys.path.append(gpydir)
 
########### DATA
# Set GISDBASE environment variable
os.environ['GISDBASE'] = gisdb
 
# import GRASS Python bindings (see also pygrass)
import grass.script as gscript
import grass.script.setup as gsetup

###########
# launch session
gsetup.init(gisbase,
            gisdb, location, mapset)
 
gscript.message('Current GRASS GIS 7 environment:')
print gscript.gisenv()

""" 
gscript.message('Available raster maps:')
for rast in gscript.list_strings(type = 'rast'):
    print rast
 
gscript.message('Available vector maps:')
for vect in gscript.list_strings(type = 'vect'):
    print vect
""" 


# Thinning prevents double-counting, but I also want to make sure that I don't miss cells that get to coast in between thinned areas.
# Will have to think about this again.

from grass import script as grass

def exists(name, datatype):
  YN = len(grass.parse_command('g.list', type=datatype, pattern=name))
  return YN

dataoutdir = '/home/awickert/Dropbox/Papers/InProgress/26to0kaHadCM3'

isll = grass.parse_command('g.proj', flags='g')['epsg'] == '4326'

ops = sorted(grass.parse_command('g.list', type='rast', patt='ocean_plus_shore_*').keys())
ages = []
#agesint = []
for opsi in ops:
  ages.append(opsi[-6:])
  #agesint.append(int(opsi[-6:]))

# Rolling start
ages2 = ages*2 # Stack the list
ages_selected_order = ages2[sts:len(ages)+sts]

os.chdir(dataoutdir)

# Lats and lons for export
ncfiles_for_mask__name = sorted(glob.glob('/home/awickert/Dropbox/Papers/InProgress/26to0kaHadCM3/GIS/ocean_masks/*.nc'))[nstart:nend]

#ages = ages[:6]

ii = 0
for ncfile_for_mask__name in ncfiles_for_mask__name:

  # VERY SPECIFIC TO THIS DATA SET -- IS HARD-CODED HERE BUT WILL NEED TO BE CHAGNED IN GENERAL
  ncfile_basename = os.path.basename(ncfile_for_mask__name).split('.')[0] 
  # Output file name
  outname = '/home/awickert/Dropbox/Papers/InProgress/26to0kaHadCM3/MeltwaterInputFiles/DirectOutput/'+location+'_'+ncfile_basename+'_Q_m3_s.nc'
  # Input GIS ocean grid: I have to import this *and*
  sea_grid_points = 'sea_grid_points_'+ncfile_basename

  if os.path.isfile(outname):
    print ""
    print "*****"
    print 'Skipping ocean mask', ncfile_basename
    print 'Output file already exists.'
    print "*****"
    print ""
  else:
    print ""
    print "*****"
    print 'Using ocean mask', ncfile_basename
    print "*****"
    print ""

    #if exists(sea_grid_points, 'vector') == False:
    if True:
    # Repair!!!!
      try:
        grass.run_command('v.db.droptable', map=sea_grid_points, flags='f')
      except:
        try:
          grass.run_command('v.db.droptable', table=sea_grid_points, flags='f')
        except:
          pass
      grass.run_command('v.proj', location='ocean_model_grid', input=sea_grid_points, overwrite=True, quiet=True)
        # Could do this entirely within GRASS, but I'll keep querying the external files
        #grass.run_command('r.proj', location='ocean_model_grid', input=ncfile_basename)
      #discharge_grid = garray.array()

    grass.run_command('g.region', rast='topo_000000')

    for age in ages_selected_order:
      print age
      #print isll
      # Abs because negative just means that there is offmap drainage -- happens when it hits the coast, should flag 
      # to maintain this positive in fugure revisions.
      # Choose depending on whether I want meltwater or full runoff
      # grass.mapcalc('discharge_to_coast_'+age+' = abs('+'ocean_plus_shore_'+age+' + accumulation_'+age+')', overwrite=True)
      # RASTER TO VECTOR
      grass.run_command('g.region', rast='topo_000000')
      #if exists('discharge_to_coast_'+age, 'raster') == False:  #  ncfile_basename+'_'+
      if True:
        grass.mapcalc('discharge_to_coast_'+ncfile_basename+'_'+age+' = abs('+'ocean_plus_shore_'+age+' + accumulation_ice_'+age+')', overwrite=True, quiet=True)
        grass.run_command('r.null', map='discharge_to_coast_'+ncfile_basename+'_'+age, setnull=0, quiet=True) # speeds up vector map creation
      #if isll:
        #grass.run_command('g.region', rast='topo_000000') Replaced with this, but why bother? already there!
        #grass.run_command('g.region', w=-180, e=180) # THIS MAY HAVE SUNK THE FIRST SET OF RUNS!!!!
      #if exists('discharge_to_coast_'+ncfile_basename+'_'+age, 'vector') == False:
      if True:
        try:
          grass.run_command('r.to.vect', input='discharge_to_coast_'+ncfile_basename+'_'+age, output='discharge_to_coast_'+ncfile_basename+'_'+age, type='point', column='discharge_m3_s', overwrite=True, quiet=True)
          #grass.run_command('v.db.dropcolumn', map='discharge_to_coast_'+ncfile_basename+'_'+age, columns='sea_grid_lon,sea_grid_lat', quiet=True)
          grass.run_command('v.db.addcolumn', map='discharge_to_coast_'+ncfile_basename+'_'+age, columns='sea_grid_lon double precision, sea_grid_lat double precision', quiet=True)
          tmp = grass.vector_db_select('discharge_to_coast_'+ncfile_basename+'_'+age, columns='sea_grid_lat').values()[0].values()
          print "Computing lat, lon..."
          if tmp[0] == ['']:
            if isll:
              grass.run_command('v.distance', from_='discharge_to_coast_'+ncfile_basename+'_'+age, to=sea_grid_points, upload='to_x,to_y', column='sea_grid_lon,sea_grid_lat')
            else:
              grass.run_command('v.distance', from_='discharge_to_coast_'+ncfile_basename+'_'+age, to=sea_grid_points, upload='to_attr', to_column='lon', column='sea_grid_lon')
              grass.run_command('v.distance', from_='discharge_to_coast_'+ncfile_basename+'_'+age, to=sea_grid_points, upload='to_attr', to_column='lat', column='sea_grid_lat')
        except:
          print "Error or No discharge points!"
        #else:
        #  print "Discharge previously calculated; using old calculation."
    print ""
    print "***"
    print "Output Step"
    print "***"
    print ""

    """
    ii += 1

    print ""
    print "*****"
    print ii/float(len(ncfiles_for_mask__name)) * 100, '%'
    print "*****"
    print ""
    
    # UNINDENT THE NEXT FEW LINES TO RUN THESE STANDALONE
    #################
    # OUTPUT NETCDF #
    #################

    ii = 0
    for ncfile_for_mask__name in ncfiles_for_mask__name:

    # VERY SPECIFIC TO THIS DATA SET -- IS HARD-CODED HERE BUT WILL NEED TO BE CHAGNED IN GENERAL
    ncfile_basename = os.path.basename(ncfile_for_mask__name).split('.')[0] 
    # Output file name
    outname = '/home/awickert/Dropbox/Papers/InProgress/26to0kaHadCM3/MeltwaterInputFiles/'+location+'_'+ncfile_basename+'_Q_m3_s.nc'
    # Input GIS ocean grid: I have to import this *and*
    sea_grid_points = 'sea_grid_points_'+ncfile_basename
    """

    """
    if os.path.isfile(outname):
      print ""
      print "*****"
      print 'Skipping ocean mask', ncfile_basename
      print 'Output file already exists.'
      print "*****"
      print ""
    else:
      print ""
      print "*****"
      print 'Using ocean mask', ncfile_basename
      print "*****"
      print ""
    """

    """
    Qout = []
    t = []

    for age in ages:
      print ""
      print "***"
      print age
      print "***"
      print ""

      ncfile_for_mask = NetCDFFile(ncfile_for_mask__name, 'r')

      testgrid = 1 - ncfile_for_mask.variables['lsm'].getValue()
      testgrid[testgrid == 0] = np.nan

      # lsm = land-sea mask. 0 over ocean, 1 over land.
      discharge_grid = 0 * ncfile_for_mask.variables['lsm'].getValue() # Just a grid of the right size
                                                                       # Masking done in GRASS GIS location
      # 0-360!!!!!!
      lats = ncfile_for_mask.variables['latitude'].getValue()
      elons = ncfile_for_mask.variables['longitude'].getValue()
      #lons = elons.copy()
      #lons[lons>180] -= 360 -- could test for this, but know that this set has 0--360 in Qll

      # Any possible floating point precision issues can be rounded;
      Qll = np.array(grass.vector_db_select('discharge_to_coast_'+ncfile_basename+'_'+age).values()[0].values(), dtype=float)
      
      for row in Qll:
        # Summing these into gridded bins here
        discharge_grid[lats == round(row[-1],3), elons == round(row[-2],2)] += row[1]
        #discharge_grid[np.asarray(np.ix_(lats == round(row[-1],3), lons == round(row[-2],2))).squeeze()]

      t.append(age)
      Qout.append(discharge_grid.copy()) # "copy" important! otherwise points to zeroed grid.
      print "Total discharge = ", np.sum(Qout[-1]), 'm3/s'
      discharge_grid *= 0
    """

  """
  # Explicitly start GRASS GIS before running this.
  # Writes pre-calculated grids to NetCDF

  from Scientific.IO.NetCDF import NetCDFFile
  import numpy as np
  import shutil
  import os
  import sys
  import subprocess
  import glob
  import sys
  from grass import script as grass

  location = str(grass.parse_command('g.gisenv', get='LOCATION_NAME').keys()[0])

  def exists(name, datatype):
    YN = len(grass.parse_command('g.list', type=datatype, pattern=name))
    return YN

  ncfiles_for_mask__name = sorted(glob.glob('/home/awickert/Dropbox/Papers/InProgress/26to0kaHadCM3/GIS/ocean_masks/*.nc'))

  # Define ages
  ops = sorted(grass.parse_command('g.list', type='rast', patt='ocean_plus_shore_*').keys())
  ages = []
  #agesint = []
  for opsi in ops:
    ages.append(opsi[-6:])
    #agesint.append(int(opsi[-6:]))
  """


  #################
  # OUTPUT NETCDF #
  #################

  """
  ii = 0
  for ncfile_for_mask__name in ncfiles_for_mask__name:
  """

  # VERY SPECIFIC TO THIS DATA SET -- IS HARD-CODED HERE BUT WILL NEED TO BE CHAGNED IN GENERAL
  ncfile_basename = os.path.basename(ncfile_for_mask__name).split('.')[0] 
  # Output file name
  outname = '/home/awickert/Dropbox/Papers/InProgress/26to0kaHadCM3/MeltwaterInputFiles/DirectOutput/'+location+'_'+ncfile_basename+'_Q_m3_s.nc'
  # Input GIS ocean grid: I have to import this *and*
  sea_grid_points = 'sea_grid_points_'+ncfile_basename

  if os.path.isfile(outname):
    print ""
    print "*****"
    print 'Skipping ocean mask', ncfile_basename
    print 'Output file already exists.'
    print "*****"
    print ""
  else:
    print ""
    print "*****"
    print 'Using ocean mask', ncfile_basename
    print "*****"
    print ""

    Qout = []
    t = []

    for age in ages:
      print ""
      print "***"
      print age
      print "***"
      print ""

      ncfile_for_mask = NetCDFFile(ncfile_for_mask__name, 'r')

      testgrid = 1 - ncfile_for_mask.variables['lsm'].getValue()
      testgrid[testgrid == 0] = np.nan

      # lsm = land-sea mask. 0 over ocean, 1 over land.
      discharge_grid = 0 * ncfile_for_mask.variables['lsm'].getValue() # Just a grid of the right size
                                                                       # Masking done in GRASS GIS location
      # N/S (standard) lats and E lons
      lats = ncfile_for_mask.variables['latitude'].getValue()
      elons = ncfile_for_mask.variables['longitude'].getValue()
      #lons = elons.copy()
      #lons[lons>180] -= 360 -- could test for this, but know that this set has 0--360 in Qll

      # Any possible floating point precision issues can be rounded;
      Qll = np.array(grass.vector_db_select('discharge_to_coast_'+ncfile_basename+'_'+age).values()[0].values(), dtype=float)
      
      for row in Qll:
        # Summing these into gridded bins here
        discharge_grid[lats == round(row[-1],3), elons == round(row[-2],2)] += row[1]
        #discharge_grid[np.asarray(np.ix_(lats == round(row[-1],3), lons == round(row[-2],2))).squeeze()]

      t.append(age)
      Qout.append(discharge_grid.copy()) # "copy" important! otherwise points to zeroed grid.
      print "Total discharge = ", np.sum(Qout[-1]), 'm3/s'
      discharge_grid *= 0

    # Towards netcdf export
    #newnc = NetCDFFile('test2.nc', 'w')
    #shutil.copyfile('qrparm.waterfix.hadcm3_bbc15ka.nc', dst)
    newnc = NetCDFFile(outname, 'w')
    newnc.createDimension('t', len(t))
    newnc.createDimension('longitude', len(elons))
    newnc.createDimension('latitude', len(lats))
    newnc.createVariable('t', 'i', ('t',))
    newnc.createVariable('longitude', 'f', ('longitude',))
    newnc.createVariable('latitude', 'f', ('latitude',))
    newnc.createVariable('discharge', 'd', ('t', 'latitude', 'longitude'))
    newnc.variables['t'][:] = t
    newnc.variables['longitude'][:] = elons
    newnc.variables['latitude'][:] = lats
    newnc.variables['discharge'][:] = np.array(Qout)
    newnc.close()

  ii += 1

  print ""
  print "*****"
  print ii/float(len(ncfiles_for_mask__name)) * 100, '%'
  print "*****"
  print ""

