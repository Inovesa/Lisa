Simple Usage
============

This is intended for someone who simply wants to plot something quickly for example.

SimplePlotter
-------------

Each Dataset in the Inovesa generated h5 files is a possible plot. Just call the corresponding function.

Plots for data with multiple axes expect a period as parameter. If this is omitted a meshplot is done.
The period is used to generate a slice in the time axis.

::

    import Lisa
    sp = Lisa.SimplePlotter("/path/to/h5")
    sp.bunch_profile(100, xunit='s')
    plt.show()
    sp.energy_spread()
    plt.show()

MultiPlot
---------

MultiPlot is the same as SimplePlotter except it works on multiple files.

::

    import Lisa
    mp = Lisa.MultiPlot()
    mp.add_file("/path/to/h5")
    mp.add_file("/path/to/second/h5")
    ...
    mp.energy_spread()  # or any other plot supported by SimplePlotter

File
----

File is an object encapsulating the h5 file. 

It has a method for each of the DataGroups in the h5 file.

Each method takes a parameter specifying the dataset to use. This parameter has to be an attribute from
Lisa.Axis (e.g. Lisa.Axis.XAXIS for spaceaxis, Lisa.Axis.DATA for data etc.)

Inovesa Parameters are available via File.parameters. It will return an h5.Attribute instance if no 
parameter is specified.

For recurring access to data it is a speed improvement to call File.preload_full("name_of_dataset").
This will read all the data to memory for faster access.

If one does not specify an axis a DataContainer containing all the data there is in the requested DataGroup 
will be returned. This object is iterable, subscriptable and has a get method that accepts Lisa.Axis properties.

Usage::
    
    import Lisa
    file = Lisa.File("/path/to/h5")
    bunch_profile_axis = file.bunch_profile(Lisa.Axis.XAXIS)
    bunch_profile = file.bunch_profile(Lisa.Axis.DATA)

Data
----

Data is an object encapsulating a File object. The benefit of this is it converts data to the given unit.

::

    import Lisa
    data = Lisa.Data("/path/to/h5")
    data.bunch_profile(Lisa.Axis.DATA, unit="c/s")  # c/s for coulomb per second.
    data.bunch_position(Lisa.Axis.XAXIS, unit="m")  # m for meter
    data.bunch_position(Lisa.Axis.XAXIS, unit="s")  # s for meter

To get data as it is saved in the h5 file use unit=None.

It is possible to pass the unit as second parameter without a keyword. (For raw data (unit=None) this is not possible).

PhaseSpace
----------

PhaseSpace is used to generate PhaseSpace plots or movies.

Use PhaseSpace.plot_ps to plot a phasespace or use PhaseSpace.phase_space_movie to generate a PhaseSpace Movie.

It is also possible to generate a movie with subtracted mean phase space using PhaseSpace.microstructure_movie.

Furthermore is it possible to extract "screenshots" from those movies by passing "extract_slice" (see

MultiPhaseSpaceMovie
--------------------

This is used to generate PhaseSpace movies from phase spaces in multiple files.

The method to generate the movie is MultiPhaseSpaceMovie.create_movie
