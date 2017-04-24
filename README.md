## Lisa - Lisa Inovesa Simulation Analysis

###Usage:

#### SimplePlotter

import Lisa
sp = Lisa.SimplePlotter("/path/to/h5")
sp.bunch_profile(100)
sp.energy_spread()
\# every dataset in the hdf5 file is a possible plot. to create it call the associated function
