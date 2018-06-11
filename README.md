## Lisa - Lisa Inovesa Simulation Analysis

[![Run Status](https://api.shippable.com/projects/59e77145a64bbc0700a423c5/badge?branch=master)](https://app.shippable.com/bitbucket/lycab/lisa)

### Usage:

This is only short introduction for very basic usage.

Detailed documentation is located in the doc directory. For a prebuilt documentation see the 'doc' branch.

#### SimplePlotter
Each Dataset in the Inovesa generated h5 files is a possible plot. Just call the corresponding function.

Plots for data with multiple axes expect a period as parameter. If this is omitted a meshplot is done.
The period is used to generate a slice in the time axis.


```python
import lisa
sp = lisa.SimplePlotter("/path/to/h5")
sp.bunch_profile(100)
sp.energy_spread()
```

#### MultiPlot
MultiPlot is the same as SimplePlotter except it works on multiple files.

```python
import lisa
mp = lisa.MultiPlot()
mp.add_file("/path/to/h5")
mp.add_file("/path/to/second/h5")
...
mp.energy_spread()  # or any other plot supported by SimplePlotter
```

#### File

File is an object encapsulating the h5 file. 

It has a method for each of the DataGroups in the h5 file.

Each method takes a parameter specifying the dataset to use. This parameter has to be an attribute from
lisa.Axis (e.g. lisa.Axis.XAXIS for spaceaxis, lisa.Axis.DATA for data etc.)

Inovesa Parameters are available via File.parameters. It will return an h5.Attribute instance if no 
parameter is specified.

For recurring access to data it is a speed improvement to call File.preload_full("name_of_dataset").
This will read all the data to memory for faster access.

If one does not specify an axis a DataContainer containing all the data there is in the requested DataGroup 
will be returned. This object is iterable, subscriptable and has a get method that accepts lisa.Axis properties.

Usage:

```python    
import lisa
file = lisa.File("/path/to/h5")
bunch_profile_axis = file.bunch_profile(lisa.Axis.XAXIS)
bunch_profile = file.bunch_profile(lisa.Axis.DATA)
```

#### Data

Data is an object encapsulating a File object. The benefit of this is it converts data to the given unit.

```python
import lisa
data = lisa.Data("/path/to/h5")
data.bunch_profile(lisa.Axis.DATA, unit="c")  # c for coulomb. 
data.bunch_position(lisa.Axis.XAXIS, unit="m")  # m for meter
data.bunch_position(lisa.Axis.XAXIS, unit="s")  # s for meter
```

To get data as it is saved in the h5 file use unit=None.

It is possible to pass the unit as second parameter without a keyword. (For raw data (unit=None) this is not possible).

#### PhaseSpace
PhaseSpace is used to generate PhaseSpace plots or movies.

Use PhaseSpace.plot_ps to plot a phasespace or use PhaseSpace.ps_movie to generate a PhaseSpace Movie

#### MultiPhaseSpaceMovie
This is used to generate PhaseSpace movies from phase spaces in multiple files.

The method to generate the movie is MultiPhaseSpaceMovie.create_movie
