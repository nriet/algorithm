import numpy as np
import Nio
import logging
shape = Nio.open_file(r'/nfsshare/cdbdata/algorithm/conductor/WMFS/EXTPRE/ysq/map/china_mask3.shp', "r")
lon = np.ravel(shape.variables["x"][:])
lat = np.ravel(shape.variables["y"][:])
segments = shape.variables["segments"]
logging.info(np.shape(segments))
logging.info(np.shape(lon))
logging.info(np.shape(lat))

logging.info(np.shape(segments[:, 0]))
