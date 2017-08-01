## Lisa - Lisa Inovesa Simulation Analysis

### Usage:

This is only short introduction for very basic usage.

Detailed documentation is located in the doc directory. For a prebuilt documentation see the 'doc' branch.

#### SimplePlotter
Each Dataset in the Inovesa generated h5 files is a possible plot. Just call the corresponding function.

Plots for data with multiple axes expect a period as parameter. If this is omitted a meshplot is done.
The period is used to generate a slice in the time axis.


```python
import Lisa
sp = Lisa.SimplePlotter("/path/to/h5")
sp.bunch_profile(100)
sp.energy_spread()
```

#### MultiPlot
MultiPlot is the same as SimplePlotter except it works on multiple files.

```python
import Lisa
mp = Lisa.MultiPlot()
mp.add_file("/path/to/h5")
mp.add_file("/path/to/second/h5")
...
mp.energy_spread()  # or any other plot supported by SimplePlotter
```

#### File
File is an object encapsulating the h5 file. To get data use the property named as the Dataset. It
will return the axis and the data as a list.

Inovesa Parameters are available via File.parameters. It will return a h5.Attribute instance.

Properties are implemented as python properties.

For recurring access to data it is a speed improvement to call File.preload_full("name_of_dataset").
This will read all the data to memory for faster access.


#### Data
Data is an object encapsulating a File object. The benefit of this is it converts data to the given unit.

```python
import Lisa
data = Lisa.Data("/path/to/h5")
data.bunch_profile(2, unit="c")  # c for coulomb. 2 for the data (can also use 'data' as first parameter for data or 'axis0' for first axis
data.bunch_position(1, unit="m")  # m for meter
```
To get data as it is saved in the h5 file use unit=None.

It is possible to pass the unit as first parameter without a keyword. (For raw data (unit=None) this is not possible).

#### PhaseSpace
PhaseSpace is used to generate PhaseSpace plots or movies.

Use PhaseSpace.plot_ps to plot a phasespace or use PhaseSpace.ps_movie to generate a PhaseSpace Movie

#### MultiPhaseSpaceMovie
This is used to generate PhaseSpace movies from phase spaces in multiple files.

The method to generate the movie is MultiPhaseSpaceMovie.create_movie
