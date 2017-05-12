#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Created on Mon Mar  6 13:48:14 2017

@author: patrick
"""

import matplotlib.pyplot as plt
import matplotlib.animation as anim
import matplotlib

import numpy as np
import glob
from numbers import Number

import sys

##video stuff
from moviepy.video.io.bindings import mplfig_to_npimage
from moviepy.video.VideoClip import DataVideoClip
from moviepy.editor import concatenate_videoclips

import textwrap

from ..file import File
from .config import Style

colors = [(0, 0, 1, 1), (0.8, 0.4, 0, 0.6), (1, 0, 1, 0.6), (0, 1, 1, 0.6), (1, 0, 0, 0.6),
          (0, 1, 0, 0.4)]
trans_value = 0.8

_simple_plotter_plot_methods = []

warn = lambda x: sys.stderr.write("Warning: "+str(x)+"\n")

def setup_plots():  # todo arguments for latexify
    from blhelpers.plot_helpers import latexify
    latexify()

class SimplePlotter(object):
    """
    A Simple Plot Helper Class
    It takes a Filename to the Constructor.
    Each Method takes a optional label and a optional figure (kwarg fig)
    If fig is given the data is plotted into this figure
    """
    def __init__(self, filef, unit_connector='in'):
        """
        Initialise a Simple Plotter instance
        :param filef: The file name of this Plotter or a Lisa.File instance
        """
        if isinstance(filef, File):
            self._file = filef
        else:
            self._file = File(filef)
        self.current = self._file.parameters["BunchCurrent"]
        self.unit_connector = unit_connector

    def plot(func):
        """
        Decorator to reuse plotting methods for different data
        """
        _simple_plotter_plot_methods.append(func.__name__)
        def decorated(*args, **kwargs):
            """
            General Options (always use as keywords):
            :param fig: (optional) the figure to plot in
            :param label: (optional) the label for this plot (legend)
            :param scale_factor: (optional) a scale factor Note: This does not modify the labels
            :param use_offset: (optional) a bool if one wants an offset on yaxis or not
            :param force_exponential_x: (optional) a bool if one wants to force exponential notation on xaxis or not
            :param force_exponential_y: (optional) a bool if one wants to force exponential notation on yaxis or not
            :param plt_args: (optional) dictionary with arguments to the displaying function
            """
            scale_factor = kwargs["scale_factor"] if "scale_factor" in kwargs else 1.
            if ("fig" in kwargs and isinstance(kwargs["fig"], plt.Figure)):
                fig = kwargs["fig"]
                ax = fig.add_subplot(111)
            else:
                fig = plt.figure(tight_layout=True)
                ax = fig.add_subplot(111)
                kwargs["axes"] = ax
            x, y, xlabel, ylabel = func(*args, **kwargs) # arguments contain self object
            alpha = None
            if 'alpha' in kwargs.get("plt_args", {}):
                warn("'alpha' in plt_args will override auto generated alpha values for multiple plots.")
                alpha = kwargs.get("plt_args").get("alpha")
                del kwargs.get("plt_args")['alpha']
            if 'label' in kwargs.get("plt_args", {}):
                warn("'label' in plt_args is invalid. Use label in arguments. Will ignore.")
                del kwargs.get("plt_args")['labemporl']
            if(hasattr(fig, "num_of_plots")):
                nop = fig.num_of_plots
                fig.num_of_plots += 1
            else:
                nop = 0
                fig.num_of_plots = 1
            if "label" in kwargs:
                alpha = ((trans_value if nop > 0 else 1) if alpha is None else alpha)
                ax.plot(x, np.array(y)*scale_factor, label=kwargs["label"], alpha=alpha, **kwargs.get("plt_args", {}))
                ax.legend(loc="best")
            else:
                alpha = ((trans_value if nop > 0 else 1) if alpha is None else alpha)
                ax.plot(x, np.array(y)*scale_factor, alpha=alpha, **kwargs.get("plt_args", {}))
            if(xlabel != "" and ax.get_xlabel()!="" and xlabel!=ax.get_xlabel()):
                xlabel = ax.get_xlabel()+"\n"+xlabel
            if(ylabel != "" and ax.get_ylabel()!="" and ylabel!=ax.get_ylabel()):
                ylabel = ax.get_ylabel()+"\n"+ylabel
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            s = Style()
            s.apply_to_fig(fig)
            if kwargs.get('use_offset', None) is not None:
                ax.get_yaxis().get_major_formatter().set_useOffset(kwargs.get('use_offset'))
            if kwargs.get("force_exponential_x", False):
                ax.get_xaxis().get_major_formatter().set_powerlimits((0, 0))
            if kwargs.get("force_exponential_y", False):
                ax.get_yaxis().get_major_formatter().set_powerlimits((0, 0))
            return fig
        decorated.__name__ = func.__name__
        decorated.__doc__ = textwrap.dedent(decorated.__doc__)+"\nSpecial Options for this plot:"+\
                            textwrap.dedent(func.__doc__)
        return decorated

    def meshPlot(func):
        """
        Decorator to reuse plotting methods and to unify colormesh plots and normal line plots
        """
        def decorated(*args, **kwargs):
            """
            General Options (always use as keywords):
            :param fig: (optional) the figure to plot in
            :param label: (optional) the label for this plot (legend) (if line plot)
            :param norm: (optional) the norm to use if pcolormesh (default LogNorm)
            :param colormap: (optional) the colormap for pcolormesh to use (default PuBu)
            :param force_bad_to_min: (optional) force bad values (e.g. negative or zero in LogNorm) of colorbar to minimum color of colorbar
            :param force_exponential_x: (optional) a bool if one wants to force exponential notation on xaxis or not
            :param force_exponential_y: (optional) a bool if one wants to force exponential notation on yaxis or not
            :param plt_args: (optional) dictionary with arguments to the displaying function
            :param period: (optional) the period to use. If not given will plot all data as pcolormesh
            """
            period, x, y, z, xlabel, ylabel, zlabel = func(*args, **kwargs)
            if period is not None:
                if period not in y:
                    print("Interpolating for usable period (using nearest): ",end="")
                idx = np.argmin(np.abs(np.array(y)-period))
                if period not in y:
                    print(y[idx])
                @SimplePlotter.plot
                def dummy(x, z, xlabel, zlabel, *args, **kwargs):
                    if hasattr(z, 'unit_function'):
                        z = z.unit_function(idx)
                    else:
                        z = z[idx]
                    return(x, z, xlabel, zlabel)
                return dummy(x, z, xlabel, zlabel, **kwargs)

            if ("fig" in kwargs and isinstance(kwargs["fig"], plt.Figure)):
                fig = kwargs["fig"]
                ax = fig.add_subplot(111)
            else:
                fig = plt.figure()
                ax = fig.add_subplot(111)
                kwargs["axes"] = ax
            if 'norm' in kwargs:
                norm = kwargs['norm']
            else:
                norm = matplotlib.colors.LogNorm()
            # warn if values in kwargs and plt_args
            if 'norm' in kwargs.get("plt_args", {}):
                warn("'norm' is already in arguments, duplicate in plt_args, will not use norm in plt_args")
                del kwargs.get("plt_args")['norm']
            if 'cmap' in kwargs.get("plt_args", {}):
                warn("'cmap' will be set by this method. use colormap argument instead of cmap in plt_args.\n"+\
                     "will ignore cmap in plt_args.")
                del kwargs.get("plt_args")['cmap']
            pm = ax.pcolormesh(x, y, z, norm=norm, cmap=kwargs.get("colormap", "PuBu"), **kwargs.get("plt_args", {}))
            ax.set_xlabel(xlabel)  # TODO: What?
            ax.set_ylabel(ylabel)
            if kwargs.get("force_bad_to_min", False):
                pm.get_cmap().set_bad((pm.get_cmap()(pm.get_clim()[0])))

            if kwargs.get("force_exponential_x", False):
                ax.get_xaxis().get_major_formatter().set_powerlimits((0, 0))
            if kwargs.get("force_exponential_y", False):
                ax.get_yaxis().get_major_formatter().set_powerlimits((0, 0))
            fig.colorbar(pm).set_label(zlabel);
            s = Style()
            s.apply_to_fig(fig)
            return fig

        decorated.__name__ = func.__name__
        decorated.__doc__ = textwrap.dedent(decorated.__doc__)+"\nSpecial Options for this plot:"+\
                            textwrap.dedent(func.__doc__)
        return decorated

    def _select_label(self, kwargs, key, values, label, unit_for_label):
        """
        Select the correct label for the given kwargs.
        Usage example:
            label = self._select_label(kwargs, 'xunit', ['ts','seconds'],
                                                       ['T in # Synchrotron Periods', 'T in s'])
        The first value/label is default (if key not in kwargs or value is not in values)
        If the value of key in kwargs is 'raw' a label with + '(raw)' is returned
        """
        uc = kwargs.get('connector', self.unit_connector)
        if key in kwargs and kwargs[key] not in values and kwargs[key] != 'raw':
            warn("'{}' is not a valid '{}' for this plot".format(kwargs[key], key))
        if kwargs.get(key) == 'raw':
            return ' '.join([label, '(raw)'])
        if kwargs.get(key) in values:
            return ' '.join([label, uc, unit_for_label[values.index(kwargs.get(key))]])
        else:
            return ' '.join([label, uc, unit_for_label[0]])

    def _select_unit(self, kwargs, key, data, values, attributes, dataAttrs=None):
        """
        Select the correct unit and apply to data.
        Usage example:
          data = self._select_unit(kwargs, 'xunit', data, ['ts', 'seconds'], [None, 'Factor4Seconds'])
        A attribute None is treated as "do not modify data".
        The first value/attribute is default (if key not in kwargs or value not in values)
        If the value of key in kwargs is 'raw' the raw data is returned
        """
        if key in kwargs and kwargs[key] not in values and kwargs[key] != 'raw':
            warn("'{}' is not a valid '{}' for this plot".format(kwargs[key], key))
        if kwargs.get(key) == 'raw':
            return data
        if kwargs.get(key) in values:
            attr = attributes[values.index(kwargs.get(key))]
        else:
            attr = attributes[0]
        if attr is None:
            return data
        attrs = dataAttrs if dataAttrs is not None else data.attrs
        factor = attrs[attr]
        if factor == 0.0:
            factor = 1.0
            warn(attr + " is 0.0 in datafile using 1.0")
        return data * np.float64(factor)

    def _get_unit_and_label(self, kwargs, key, values, label, unit_for_label, attributes, data):
        """
        Convenience wrapper around self._select_unit and self._select_label. This also reduces
        the risk of using a different order in the call of unit and label so unit and label always match
        """
        return (self._select_unit(kwargs, key, data, values, attributes),
                self._select_label(kwargs, key, values, label, unit_for_label))

    @plot
    def energy_spread(self, **kwargs):
        """
        kwargs:
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "eV", "raw"
        """
        x, y = self._file.energy_spread
        x, xlabel = self._get_unit_and_label(kwargs, 'xunit', ['ts', 'seconds'],
                                             'T', ['# Synchrotron Periods', 's'],
                                             [None, 'Factor4Seconds'], x)

        y, ylabel = self._get_unit_and_label(kwargs, 'yunit', ['eV'], 'Energy Spread', ['eV'],
                                             ['Factor4ElectronVolts'], y)
        return (x, y, xlabel, ylabel)

    @meshPlot
    def bunch_profile(self, *args, **kwargs):
        """
        Plot the bunch_profile either as line plot or as pcolormesh
        to plot as line pass either the period as first argument or a keyword argument period
        Note: if yunit is passed period is in that unit, else in default value.
        kwargs: (first value is default)
          * xunit: possible values: "meters", "seconds", "raw"
          * yunit: possible values: "ts", "seconds", "raw"
          * zunit: possible values: "coulomb", "ampere", "raw"
          * pad_zero: True or False. Pad data to zero to avoid white lines in plot (only considered if period is None or not given)
        """
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period', None)

        x, xlabel = self._get_unit_and_label(kwargs, 'xunit', ['meters', 'seconds'], 'x', ['m', 's'],
                                             ['Factor4Meters', 'Factor4Seconds'], self._file.bunch_profile[0])
        y, ylabel = self._get_unit_and_label(kwargs, 'yunit', ['ts', 'seconds'], 'T', ['# Synchrotron Periods', 's'],
                                             [None, 'Factor4Seconds'], self._file.bunch_profile[1])
        if period is None:  # if no period provided
            z, zlabel = self._get_unit_and_label(kwargs, 'zunit', ['coulomb', 'ampere'], 'Popuation',
                                                 ['C', 'A'], ['Factor4Coulomb', 'Factor4Ampere'],
                                                 self._file.bunch_profile[2])
            if kwargs.get("pad_zero", False):
                z[np.where(z<np.float64(0.0))] = np.float64(1e-100)
        else:
            z = self._file.bunch_profile[2]
            z.unit_function = lambda period: self._select_unit(kwargs, 'zunit', z[period],
                                         ['coulomb', 'ampere'], ['Factor4Coulomb', 'Factor4Ampere'],
                                         dataAttrs=z.attrs)
            zlabel = self._select_label(kwargs, 'zunit', ['coulomb', 'ampere'], 'Population', ['C', 'A'])
        return period, x, y, z, xlabel, ylabel, zlabel


    @plot
    def bunch_length(self, **kwargs):
        """
        kwargs:
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "meters", "secons", "raw"
        """
        x, y = self._file.bunch_length
        x, xlabel = self._get_unit_and_label(kwargs, 'xunit', ['ts', 'seconds'], 'T',
                                             ['# Synchrotron Periods', 's'],
                                             [None, 'Factor4Seconds'], x)
        y, ylabel = self._get_unit_and_label(kwargs, 'yunit', ['meters', 'seconds'], 'Bunch Length',
                                             ['m', 's'], ['Factor4Meters', 'Factor4Seconds'], y)
        return (x, y, xlabel, ylabel)

    @plot
    def csr_intensity(self, **kwargs):
        """
        kwargs:
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "watt", "raw"
        """
        x, y = self._file.csr_intensity
        x, xlabel = self._get_unit_and_label(kwargs, 'xunit', ['ts', 'seconds'],
                                             'T', ['# Synchrotron Periods', 's'],
                                             [None, 'Factor4Seconds'], x)
        y, ylabel = self._get_unit_and_label(kwargs, 'yunit', ['watt'], 'CSR Intensity', ['W'],
                                             ['Factor4Watts'], y)
        return (x, y, xlabel, ylabel)

        return (self._file.csr_intensity[0], self._file.csr_intensity[1],
                "T in # Synchrotron Periods", "CSR Intensity") # TODO: Unit

    @plot
    def bunch_position(self, **kwargs):
        """
        kwargs: (first value is default)
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "meters", "seconds", "raw"
        """
        x, y = self._file.bunch_position
        x, xlabel = self._get_unit_and_label(kwargs, 'xunit', ['ts', 'seconds'], 'T',
                                             ['# Synchrotron Periods', 's'],
                                             [None, 'Factor4Seconds'], x)
        y, ylabel = self._get_unit_and_label(kwargs, 'yunit', ['meters', 'seconds'], 'Bunch Position',
                                             ['m', 's'], ['Factor4Meters', 'Factor4Seconds'], y)
        return (x, y, xlabel, ylabel)

    @plot
    def bunch_population(self, **kwargs):
        """
        kwargs: (first value is default)
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "meters", "seconds", "raw"
        """
        x, y = self._file.bunch_population
        x, xlabel = self._get_unit_and_label(kwargs, 'xunit', ['ts', 'seconds'], 'T',
                                             ['# Synchrotron Periods', 's'], [None, 'Factor4Seconds'], x)
        y, ylabel = self._get_unit_and_label(kwargs, 'yunit', ['coulomb', 'ampere'], 'Bunch Population',
                                             ['C', 'A'], ['Factor4Coulomb', 'Factor4Ampere'], y)
        return (x, y, xlabel, ylabel)

    @meshPlot
    def csr_spectrum(self, *args, **kwargs):
        """
        Plot the csr_spectrum either as line plot or as pcolormesh
        to plot as line pass either the period as first argument or a keyword argument period
        Note: if yunit is passed period is in that unit, else in default value.
        kwargs: (first value is default)
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "hertz", "raw"
          * zunit: possible values: "watt", "raw"
        """
        # NOTE: This does not seem to work
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period', None)

        x, xlabel = self._get_unit_and_label(kwargs, 'xunit', ['hertz'], 'Frequency', ['Hz'],
                                             ['Factor4Hertz'], self._file.csr_spectrum[1])
        y, ylabel = self._get_unit_and_label(kwargs, 'yunit', ['ts', 'seconds'], 'T', ['# Synchrotron Periods', 's'],
                                             [None, 'Factor4Seconds'], self._file.csr_spectrum[0])
        if period is None:  # if no period provided
            z, zlabel = self._get_unit_and_label(kwargs, 'zunit', ['watt'], 'Power', ['W'], ['Factor4Watts'],
                                                 self._file.csr_spectrum[2])
        else:
            z = self._file.csr_spectrum[2]
            z.unit_function = lambda period: self._select_unit(kwargs, 'zunit', z[period], ['watt'], ['Factor4Watts'],
                                                               dataAttrs=z.attrs)
            zlabel = self._select_label(kwargs, 'zunit', ['watt'], 'Power', ['W'])
        return period, x, y, z, xlabel, ylabel, zlabel

    @meshPlot
    def energy_profile(self, *args, **kwargs):
        """
        Plot the energy_profile either as line plot or as pcolormesh
        to plot as line pass either the period as first argument or a keyword argument period
        kwargs: (first value is default)
          * xunit: possible values: "eV", "raw"
          * yunit: possible values: "ts", "seconds", "raw"
          * zunit: possible values: "coulomb", "ampere", "raw"
        """
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period', None)

        x, xlabel = self._get_unit_and_label(kwargs, 'xunit', ['eV'], 'Energy', ['eV'],
                                             ['Factor4ElectronVolts'], self._file.energy_profile[0])
        y, ylabel = self._get_unit_and_label(kwargs, 'yunit', ['ts', 'seconds'], 'T', ['# Synchrotron Periods', 's'],
                                             [None, 'Factor4Seconds'], self._file.energy_profile[1])
        if period is None:  # if no period provided
            z, zlabel = self._get_unit_and_label(kwargs, 'zunit', ['coulomb', 'ampere'], 'Population',
                                                 ['C', 'A'], ['Factor4Coulomb', 'Factor4Ampere'],
                                                 self._file.energy_profile[2])
        else:
            z = self._file.energy_profile[2]
            z.unit_function = lambda period: self._select_unit(kwargs, 'zunit', z[period],
                                                               ['coulomb', 'ampere'],
                                                               ['Factor4Coulomb', 'Factor4Ampere'],
                                                               dataAttrs=z.attrs)
            zlabel = self._select_label(kwargs, 'zunit', ['coulomb', 'ampere'], 'Population', ['C', 'A'])
        return period, x, y, z, xlabel, ylabel, zlabel

    def impedance(self, *args, **kwargs):
        warn("Unit of x-Axis may not be correct")
        f4h = self._file.impedance[0].attrs["Factor4Hertz"]
        if f4h == 0:
            warn("Factor4Hertz is zero in datafile using 1.0")
            f4h = np.float64(1.0)
        @SimplePlotter.plot
        def real(*args, **kwargs):
            return (self._file.impedance[0]*f4h,
                   self._file.impedance[1], "Frequency in Hz", "Impedance in k$\\Omega$")
        fig = real(*args, label="Real", **kwargs)
        @SimplePlotter.plot
        def imag(*args, **kwargs):
            return (self._file.impedance[0]*f4h,
                    self._file.impedance[2], "Frequency in Hz", "Impedance in k$\\Omega$")
        return imag(fig=fig, label="Imag", **kwargs)



class MultiPlot(object):
    """
    Combine multiple files into one plot
    """
    def __init__(self):
        """
        Creates MultiPlot Instance
        No Parameters (to add files use add_file)
        """
        self._simple_plotters = []
        self._figure = plt.figure(tight_layout=True)

    def clone(self):
        """Return a copy of this instance"""
        mp = MultiPlot()
        mp._simple_plotters = self._simple_plotters
        return mp

    def add_file(self, filename, label=None):
        """
        Add a file to this instance
        :param filename: Path to the file
        :param label: (optional) the label for plots with this filename
        """
        self._simple_plotters.append((SimplePlotter(filename), label))

    def reset(self):
        """Reset this instance"""
        self._simple_plotters = []
        self._figure.clear()

    def possible_plots(self):
        """List all possible plots"""
        return _simple_plotter_plot_methods

    def __getattr__(self, attr):
        if len(self._simple_plotters) == 0:
            # return callable to prevent 'NoneType' object is not callable exception
            def warn_no_file(*args, **kwargs):
                warn("MultiPlot."+attr+" called without files to plot.")

            warn_no_file.__doc__ = "Dummy Method. Retry when files are added."
            warn_no_file.__name__ = attr
            return warn_no_file
        if hasattr(self._simple_plotters[0][0], attr):
            self._figure.clear()
            def inner(*args, **kwargs):
                kwargs["fig"] = self._figure
                for sp in self._simple_plotters:
                    if sp[1] != None:
                        kwargs["label"] = sp[1]
                    getattr(sp[0], attr)(*args, **kwargs)
                return self._figure
            inner.__name__ = attr
            inner.__doc__ = "MultiPlot."+attr+" will override 'fig' kwarg. \nIf 'label' was passed to add_file "+\
                            "'label' in kwarg will be overriden with that value for the corresponding file.\n"+\
                            "\nDelegated Options from SimplePlotter:\n"+ getattr(self._simple_plotters[0][0], attr).__doc__
            return inner
        else:
            raise Exception("MultiPlot does not have attribute " + attr)

class PhaseSpace(object):
    """
    Plot PhaseSpaces of a single Inovesa result file
    """
    class PSFigure(object):
        def __init__(self, fig, ax, im):
            self.fig = fig
            self.ax = ax
            self.im = im

    def __init__(self, file):
        if isinstance(file, File):
            self._file = file
        else:
            self._file = File(file)
        #self._figure = plt.figure()

    def clone(self):
        """
        Return a copy of this instance
        This effectively creates a new object with same file object
        """
        return PhaseSpace(self._file)

    def plot_ps(self, index):
        data = self._file.phase_space[2][index]
        fig, ax = plt.subplots(1)
        im = ax.imshow(data)
        im.set_cmap('inferno')
        return fig, ax, im

    def ps_movie(self, path, fps=None, bitrate=18000, interval=200, axis='off',
                 fr_idx=-1, to_idx=-1, autorescale=False, percentile=None):
        """
        Create a movie from the phasespace information
        :param path: the file to write the movie to if None: do not save
        :param fps: the framerate of the movie If fps is None will use the inverval parameter
        :param bitrate: the bitrate of the movie
        :param interval: the time between each phasespace
        :param axis: 'off' to hide 'on' to show
        :param fr_idx: the index of the first phasespace (-1 for first in file)
        :param to_idx: the index of the last phasespace (-1 for the last in file)
        :param autorescale: if True will autorescale each frame (will not make sense if you want to compare)
        :param percentile: if autorescale is True this won't have any effect. Will set the max of the colorrange to this percentile

        HINT: If the video looks black discard the first frame. the initial
            Phase space might be too intensive
        """
        plt.ioff()
        writer = anim.writers['ffmpeg'](metadata=dict(artist='Lisa'), bitrate=bitrate)
        fig = plt.figure(frameon=False)
        fig.set_size_inches(5,5)
        fig.subplots_adjust(left=0, bottom=0, right=1,top=1, wspace=None, hspace=None)

        lb = 0 if fr_idx == -1 else fr_idx
        ub = len(self._file.phase_space[2]) if to_idx == -1 else to_idx

        #index = [0 if fr_idx==-1 else fr_idx]
        im = [plt.imshow(self._file.phase_space[2][lb], animated=True, aspect='auto')]
        im[0].set_cmap('inferno')
        plt.axis(axis)

#        im[0].set_clim(vmin=np.min(self._file.phase_space[2]), vmax=np.max(self._file.phase_space[2]))
        if not autorescale and percentile is not None:
            im[0].set_clim(vmin=np.min(self._file.phase_space[2]), vmax=np.percentile(self._file.phase_space[2], percentile))

        def gen_data(i):
            idx = i + lb
            return self._file.phase_space[2][idx]

        def gen_image(i):
            im[0].set_data(gen_data(i))
            if autorescale:
                im[0].autoscale()
            return im

        #ani = anim.FuncAnimation(fig, gen_image, gen_data, init, interval=interval, blit=True, repeat=False)
        ani = anim.FuncAnimation(fig, gen_image, frames=ub-lb, interval=interval, blit=True, repeat=False)
        if path is not None:
            ani.save(path, writer, fps=fps)
        return ani

class MultiPhaseSpaceMovie(object):
    """
    Create Phasespace of multiple Files
    Useful to check the phasespace over multiple currenst (spectrogram)
    """
    def __init__(self, path):
        self._path = path

    def _get_current_from_cfg(self, filename):
        with open(filename+".cfg", 'r') as f:
            for line in f:
                if line.startswith("BunchCurrent"):
                    return float(line.split("=")[1])

    def create_movie(self, filename, dpi=200, size_inches=(5.5, 5.5), fps=30, autorescale=False):
        """
        Create a Movie of phasespaces
        :param filename: The filename to use for the produces video file
                         (if None, a moviepy video object will be returned)
        :param dpi(=200): the dpi of the produces video
        :param size_inches(=5.5, 5.5): tuple used for size in inces of the video
        :param fps(=30): the frames per second to use
        :param autorescale(=False): if True will autorescale each frame (will not make sense if you want to compare)
        :return: True if file produced, moviepy video instance if None as filename was given
        """
        plt.ioff()
        clips = []
        # NOTE: The use of this function in conjunction with a lambda with default
        # argument in DataVideoClip is necessary to use a "new" function for every
        # file. Otherwise the last file will override the first functions
        def dtv(dat, ps, clim):
            f = ps.plot_ps(dat)
            if autorescale:
                f[2].set_clim(clim)
            f[0].set_size_inches(*size_inches)
            f[0].dpi = dpi
            return mplfig_to_npimage(f[0])
        files = []
        for file in glob.glob(self._path+"/*.h5"):
            files.append((self._get_current_from_cfg(file), file))
        files.sort(key=lambda f: f[0], reverse=True)  # make sure it is sorted by the first entry
        clim = None
        for file in files:
            ps = PhaseSpace(file[1])
            if autorescale and clim is None:
                clim = ps.plot_ps(0)[2].get_clim()
            clips.append(DataVideoClip(range(len(ps._file.phase_space[2])), lambda dat, ps=ps, clim=clim: dtv(dat, ps, clim), fps=fps))
        if filename is None:
            return concatenate_videoclips(clips)
        else:
            if filename.endswith("gif"):
                concatenate_videoclips(clips).write_gif(filename)
            elif filename.endswith("mp4"):
                concatenate_videoclips(clips).write_videofile(filename)
            else:
                raise Exception("Wrong Filename")
        return True
