## Lisa - Lisa Inovesa Simulation Analysis

### Usage:

For detailed help on methods see the python help or docstrings.

#### SimplePlotter
Each Dataset in the inovesa generated h5 files is a possible plott. Just call the corresponding function.

Plots for data with multiple axes expect a period as parameter. If this is omitted a meshplot is done.
The period is used to generate a slice in the time axis.


```python
import Lisa
sp = Lisa.SimplePlotter("/path/to/h5")
sp.bunch_profile(100)
sp.energy_spread()
```

#### MultiPlot
MultiPlot is the same as SimploePlotter except it works on multiple files.

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

Properties are implemented as python properties. They will cache the data in memory and not read it
again from file if reaccessed.

#### Data
Data is an object encapsulating a File object. The benefit of this is it converts data to the given unit.

```python
import Lisa
data = Lisa.Data("/path/to/h5")
data.bunch_profile(unit="c")  # c for coulomb
data.bunch_position(unit="m")  # m for meter
```
To get data as it is saved in the h5 file use unit=None.

It is possible to pass the unit as first parameter without a keyword. (For raw data (unit=None) this is not possible).

#### PhaseSpace
PhaseSpace is used to generate PhaseSpace plots or movies.

Use PhaseSpace.plot_ps to plot a phasespace or use PhaseSpace.ps_movie to generate a PhaseSpace Movie

#### MultiPhaseSpaceMovie
This is used to generate PhaseSpace movies from phase spaces in multiple files.

The method to generate the movie is MultiPhaseSpaceMovie.create_movie
