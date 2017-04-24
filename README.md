## Lisa - Lisa Inovesa Simulation Analysis

### Usage:

#### SimplePlotter

```python
import Lisa
sp = Lisa.SimplePlotter("/path/to/h5")
sp.bunch_profile(100)
sp.energy_spread()
# every dataset in the hdf5 file is a possible plot. to create it call the associated function
```

#### MultiPlot

```python
import Lisa
mp = Lisa.MultiPlot()
mp.add_file("/path/to/h5")
mp.add_file("/path/to/second/h5")
...
mp.energy_spread()  # or any other plot supported by SimplePlotter
```
