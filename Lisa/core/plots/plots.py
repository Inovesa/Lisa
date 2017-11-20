#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
:Author: Patrick Schreiber
"""

import matplotlib.pyplot as plt
import matplotlib.animation as anim
import matplotlib

import numpy as np
import glob
from numbers import Number

import sys

import textwrap
from ..internals import config_options
from .animation import create_animation

if config_options.get("use_cython"):
    try:
        from ..file_cython import File, Axis
        from ..data_cython import Data
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from ..file import File, Axis
        from ..data import Data
else:
    from ..file import File, Axis
    from ..data import Data
from .config import Style, palettes
from ..internals import lisa_print
from ..utils import unit_from_attr, attr_from_unit, unit_from_spec, version15_1

colors = [(0, 0, 1, 1), (0.8, 0.4, 0, 0.6), (1, 0, 1, 0.6), (0, 1, 1, 0.6), (1, 0, 0, 0.6),
          (0, 1, 0, 0.4)]
trans_value = 0.8

_simple_plotter_plot_methods = []

warn = lambda x: sys.stderr.write("Warning: "+str(x)+"\n")


class Deprecated(Exception):
    msg = ("This is deprecated",)

def setup_plots():  # todo arguments for latexify
    """
    Setup Plots to look native in Latex documents. Subject to change.
    """
    from blhelpers.plot_helpers import latexify
    latexify()

try:
    import matplotlib2tikz as m2t
    def save_pgfplot(*args, **kwargs):
        """Wrapper around matplotlib2tikz.save"""
        m2t.save(*args, **kwargs)
except ImportError:
    pass


class SimplePlotter(object):
    """
    | A Simple Plot Helper Class.
    | It takes a Filename to the Constructor.
    | Each actual plotting function is decorated using plot or meshPlot. See those for additional parameters to each plot function.
    """
    def __init__(self, filef, unit_connector='in'):
        """
        Initialise a Simple Plotter instance
        :param filef: The file name of this Plotter or a Lisa.File instance
        :param unit_connector: The string to use between label and unit.
        """
        if isinstance(filef, File):
            self._file = filef
        else:
            self._file = File(filef)
        self._data = Data(self._file)
        self.current = self._file.parameters("BunchCurrent")
        self.unit_connector = unit_connector

    def plot(func):
        """
        Decorator to reuse plotting methods for different data. Calling one of the actual plot functions will result in calling this.
        This means the following options are available:

        General Options (always use as keywords):
        :param fig: (optional) the figure to plot in
        :param ax: (optional) the axis to use to plot
        :param label: (optional) the label for this plot (legend)
        :param scale_factor: (optional) a scale factor Note: This does not modify the labels
        :param use_offset: (optional) a bool if one wants an offset on yaxis or not
        :param force_exponential_x: (optional) a bool if one wants to force exponential notation on xaxis or not
        :param force_exponential_y: (optional) a bool if one wants to force exponential notation on yaxis or not
        :param fft: (optional) a bool if one wants to plot fft(data) instead of data or string for method to use in numpy.fft
        :param fft_padding: (optional) an integer to specify how much 0 will be padded to the data before fft default fft
        :param abs: (optional) a boolean to select if plot absolute values or direct data
        :param plt_args: (optional) dictionary with arguments to the displaying function
        :param x_log: (optional) a boolean to set the x axis to log scale
        :param y_log: (optional) a boolean to set the y axis to log scale
        """
        _simple_plotter_plot_methods.append(func.__name__)
        def decorated(*args, **kwargs):
            scale_factor = kwargs["scale_factor"] if "scale_factor" in kwargs else 1.
            if isinstance(kwargs.get("fig", None), plt.Figure):
                fig = kwargs["fig"]
                if isinstance(kwargs.get("ax", None), plt.Axes):
                    ax = kwargs.get("ax")
                else:
                    ax = fig.add_subplot(111)
            else:
                if isinstance(kwargs.get("ax", None), plt.Axes):
                    ax = kwargs.get("ax")
                    fig = ax.figure
                else:
                    fig = plt.figure(tight_layout=True)
                    ax = fig.add_subplot(111)
            if kwargs.get("x_log"):
                ax.set_xscale('log')
            if kwargs.get("y_log"):
                ax.set_yscale('log')
            x, y, xlabel, ylabel = func(*args, **kwargs)  # arguments contain self object
            if kwargs.get("fft"):
                ylabel = "FFT("+ylabel+")"
                xlabel = "Frequency like (1/("+xlabel+"))"
                if kwargs.get("fft_padding"):
                    y = np.append([0]*kwargs.get("fft_padding"), y)
                    y = np.append(y, [0]*kwargs.get("fft_padding"))
                if kwargs.get("fft") is True:
                    x = np.fft.fftfreq(x.shape[0]+2*kwargs.get("fft_padding", 0), x[1]-x[0])
                    y = np.fft.fft(y)
                else:
                    x = getattr(np.fft, kwargs.get("fft")+"freq")(x.shape[0]+2*kwargs.get("fft_padding", 0), x[1]-x[0])
                    y = getattr(np.fft, kwargs.get("fft"))(y)
            if kwargs.get("abs"):
                y = np.abs(y)
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
        decorated.__doc__ = "This method is decorated. See SimplePlotter.plot for additional parameters"
        if func.__doc__ is not None:
            decorated.__doc__ += "\nSpecial Options for this plot:"+textwrap.dedent(func.__doc__)
        return decorated

    def meshPlot(func):
        """
        Decorator to reuse plotting methods and to unify colormesh plots and normal line plots.
        Calling one of the actual plot functions will result in calling this.
        This means the following options are available:

        General Options (always use as keywords):
        :param fig: (optional) the figure to plot in
        :param ax: (optional) the axis to use to plot
        :param label: (optional) the label for this plot (legend) (if line plot)
        :param norm: (optional) the norm to use if pcolormesh (default LogNorm)
        :param colormap: (optional) the colormap for pcolormesh to use (default PuBu)
        :param force_bad_to_min: (optional) force bad values (e.g. negative or zero in LogNorm) of colorbar to minimum color of colorbar
        :param force_exponential_x: (optional) a bool if one wants to force exponential notation on xaxis or not
        :param force_exponential_y: (optional) a bool if one wants to force exponential notation on yaxis or not
        :param plt_args: (optional) dictionary with arguments to the displaying function
        :param period: (optional) the period to use. If not given will plot all data as pcolormesh (use parameters from plot)
        :param use_index: (optional) Use period as index in data and not synchrotron period (default False)
        :param mean_range: (optional) If given plot a normal plot but with data from mean of the given range (use parameters from plot)
        """
        _simple_plotter_plot_methods.append(func.__name__)
        def decorated(*args, **kwargs):
            period, x, y, z, xlabel, ylabel, zlabel = func(*args, **kwargs)
            if period is not None:
                print_interpol = False
                if kwargs.get("use_index", False):
                    idx = period
                else:
                    if period not in y:
                        lisa_print("Interpolating for usable period (using nearest): ", end="", debug=False)
                        print_interpol = True
                    if period < 0:
                        period = np.max(y)+period
                    idx = np.argmin(np.abs(np.array(y)-period))
                args[0]._last_interpol_idx = idx
                # if period not in y and not kwargs.get("use_index", False):
                if print_interpol:
                    lisa_print(y[idx], debug=False)
                @SimplePlotter.plot
                def dummy(x, z, xlabel, zlabel, *args, **kwargs):
                    if hasattr(z, 'unit_function'):
                        z = z.unit_function(idx)
                    else:
                        z = z[idx]
                    return(x, z, xlabel, zlabel)
                return dummy(x, z, xlabel, zlabel, **kwargs)

            if kwargs.get("mean_range", None) is not None:
                range = kwargs.get("mean_range")
                z_mean = np.mean(z[range[0]:range[1]], axis=0)
                zlabel += " (mean over range {})".format(range)
                @SimplePlotter.plot
                def dummy(x, z, xlabel, zlabel, *args, **kwargs):
                    return(x, z, xlabel, zlabel)
                return dummy(x, z_mean, xlabel, zlabel, **kwargs)


            if isinstance(kwargs.get("fig", None), plt.Figure):
                fig = kwargs["fig"]
                if isinstance(kwargs.get("ax", None), plt.Axes):
                    ax = kwargs.get("ax")
                else:
                    ax = fig.add_subplot(111)
            else:
                if isinstance(kwargs.get("ax", None), plt.Axes):
                    ax = kwargs.get("ax")
                    fig = ax.figure
                else:
                    fig = plt.figure(tight_layout=True)
                    ax = fig.add_subplot(111)

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
            fig.colorbar(pm).set_label(zlabel)
            s = Style()
            s.apply_to_fig(fig)
            return fig

        decorated.__name__ = func.__name__
        decorated.__doc__ = "This method is decorated. See SimplePlotter.plot for additional parameters"
        if func.__doc__ is not None:
            decorated.__doc__ += "\nSpecial Options for this plot:"+textwrap.dedent(func.__doc__)
        return decorated

    def _select_label(self, kwargs, key, values, label, unit_for_label):
        raise Deprecated()
        """
        | Select the correct label for the given kwargs.
        | Usage example:
        |     label = self._select_label(kwargs, 'xunit', ['ts','seconds'],
        |                                               ['T in # Synchrotron Periods', 'T in s'])
        | The first value/label is default (if key not in kwargs or value is not in values)
        | If the value of key in kwargs is 'raw' a label with + '(raw)' is returned
        """
        lisa_print("Selecting Label", "kwargs", kwargs, "key", key, "values", values, "label", label, "unit_for_label", unit_for_label)
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
        raise Deprecated()
        """
        | Select the correct unit and apply to data.
        | Usage example:
        |   data = self._select_unit(kwargs, 'xunit', data, ['ts', 'seconds'], [None, 'Factor4Seconds'])
        | A attribute None is treated as "do not modify data".
        | The first value/attribute is default (if key not in kwargs or value not in values)
        | If the value of key in kwargs is 'raw' the raw data is returned
        """
        lisa_print("Selecting Unit", "kwargs", kwargs, "key", key, "values", values, "attributes", attributes, "dataAttrs", dataAttrs)
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
        raise Deprecated()
        """
        Convenience wrapper around self._select_unit and self._select_label. This also reduces
        the risk of using a different order in the call of unit and label so unit and label always match
        """
        return (self._select_unit(kwargs, key, data, values, attributes),
                self._select_label(kwargs, key, values, label, unit_for_label))

    def _unit_and_label(self, kwargs, idx, axis, data, default, label, gen_sub=False):
        if gen_sub:
            d = getattr(self._data, data+"_raw")(idx)
            unit = unit_from_spec(kwargs.get(axis+"unit", default))
            d.unit_function = lambda idx, _data=data, _idx=idx, _unit=unit: getattr(self._data, _data)(_idx, unit=_unit, sub_idx=idx)
        else:
            d = getattr(self._data, data)(idx, unit=kwargs.get(axis+"unit", default))
        lab = label + " in " + unit_from_spec(kwargs.get(axis+"unit", default))
        return d, lab

    @plot
    def energy_spread(self, **kwargs):
        """
        kwargs:
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "eV", "raw"
        """
        x, xlabel = self._unit_and_label(kwargs, Axis.TIME, 'x', 'energy_spread', 'ts', "T")
        y, ylabel = self._unit_and_label(kwargs, Axis.DATA, 'y', 'energy_spread', 'eV', "Energy Spread")
        return (x, y, xlabel, ylabel)

    @meshPlot
    def bunch_profile(self, *args, **kwargs):
        """
        | Plot the bunch_profile either as line plot or as pcolormesh
        | to plot as line pass either the period as first argument or a keyword argument period
        | Note: if yunit is passed period is in that unit, else in default value.

        kwargs: (first value is default)
          * xunit: possible values: "meters", "seconds", "raw"
          * yunit: possible values: "ts", "seconds", "raw"
          * zunit: possible values: "coulomb", "ampere", "raw"
          * pad_zero: True or False. Pad data to zero to avoid white lines in plot (only considered if period is None or not given)
        """
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period', None)
        x, xlabel = self._unit_and_label(kwargs, Axis.XAXIS, 'x', 'bunch_profile', 'm', "x")
        y, ylabel = self._unit_and_label(kwargs, Axis.TIME, 'y', 'bunch_profile', 'ts', "T")
        dataunit = "c" if self._file.version < version15_1 else "cpnbl"
        if period is None:  # if no period provided
            z, zlabel = self._unit_and_label(kwargs, Axis.DATA, 'z', 'bunch_profile', dataunit, "Population")
            if kwargs.get("pad_zero", False):
                z[np.where(z<np.float64(0.0))] = np.float64(1e-100)
        else:
            z, zlabel = self._unit_and_label(kwargs, Axis.DATA, 'z', 'bunch_profile', dataunit, "Population", gen_sub=True)
        return period, x, y, z, xlabel, ylabel, zlabel


    @plot
    def bunch_length(self, **kwargs):
        """
        kwargs:
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "meters", "secons", "raw"
        """
        x, xlabel = self._unit_and_label(kwargs, Axis.TIME, 'x', 'bunch_length', 'ts', "T")
        y, ylabel = self._unit_and_label(kwargs, Axis.DATA, 'y', 'bunch_length', 'm', "Bunch Length")
        return (x, y, xlabel, ylabel)

    @plot
    def csr_intensity(self, **kwargs):
        """
        kwargs:
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "watt", "raw"
        """
        x, xlabel = self._unit_and_label(kwargs, Axis.TIME, 'x', 'csr_intensity', 'ts', "T")
        y, ylabel = self._unit_and_label(kwargs, Axis.DATA, 'y', 'csr_intensity', 'W', "CSR Intensity")
        return (x, y, xlabel, ylabel)

    @plot
    def bunch_position(self, **kwargs):
        """
        kwargs: (first value is default)
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "meters", "seconds", "raw"
        """
        x, xlabel = self._unit_and_label(kwargs, Axis.TIME, 'x', 'bunch_position', 'ts', "T")
        y, ylabel = self._unit_and_label(kwargs, Axis.DATA, 'y', 'bunch_position', 'm', "Bunch Position")
        return (x, y, xlabel, ylabel)

    @plot
    def bunch_population(self, **kwargs):
        """
        kwargs: (first value is default)
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "meters", "seconds", "raw"
        """
        x, xlabel = self._unit_and_label(kwargs, Axis.TIME, 'x', 'bunch_population', 'ts', "T")
        y, ylabel = self._unit_and_label(kwargs, Axis.DATA, 'y', 'bunch_population', 'c', "Bunch Population")
        return (x, y, xlabel, ylabel)

    @meshPlot
    def csr_spectrum(self, *args, **kwargs):
        """
        | Plot the csr_spectrum either as line plot or as pcolormesh
        | to plot as line pass either the period as first argument or a keyword argument period
        | Note: if yunit is passed period is in that unit, else in default value.

        kwargs: (first value is default)
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "hertz", "raw"
          * zunit: possible values: "watt", "raw"
        """
        # NOTE: This does not seem to work
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period', None)
        x, xlabel = self._unit_and_label(kwargs, Axis.FAXIS, 'x', 'csr_spectrum', 'Hz', "Frequency")
        y, ylabel = self._unit_and_label(kwargs, Axis.TIME, 'y', 'csr_spectrum', 'ts', "T")
        if period is None:  # if no period provided
            z, zlabel = self._unit_and_label(kwargs, Axis.DATA, 'z', 'csr_spectrum', 'wphz', "Power")
            if kwargs.get("pad_zero", False):
                z[np.where(z<np.float64(0.0))] = np.float64(1e-100)
        else:
            z, zlabel = self._unit_and_label(kwargs, Axis.DATA, 'z', 'csr_spectrum', 'wphz', "Power", gen_sub=True)
        return period, x, y, z, xlabel, ylabel, zlabel

    @meshPlot
    def energy_profile(self, *args, **kwargs):
        """
        | Plot the energy_profile either as line plot or as pcolormesh
        | to plot as line pass either the period as first argument or a keyword argument period

        kwargs: (first value is default)
          * xunit: possible values: "eV", "raw"
          * yunit: possible values: "ts", "seconds", "raw"
          * zunit: possible values: "coulomb", "ampere", "raw"
        """
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period', None)
        x, xlabel = self._unit_and_label(kwargs, Axis.EAXIS, 'x', 'energy_profile', 'eV', "Energy")
        y, ylabel = self._unit_and_label(kwargs, Axis.TIME, 'y', 'energy_profile', 'ts', "T")
        dataunit = "c" if self._file.version < version15_1 else "cpnes"
        if period is None:  # if no period provided
            z, zlabel = self._unit_and_label(kwargs, Axis.DATA, 'z', 'energy_profile', dataunit, "Population")
            if kwargs.get("pad_zero", False):
                z[np.where(z<np.float64(0.0))] = np.float64(1e-100)
        else:
            z, zlabel = self._unit_and_label(kwargs, Axis.DATA, 'z', 'energy_profile', dataunit, "Population", gen_sub=True)
        return period, x, y, z, xlabel, ylabel, zlabel

    def impedance(self, *args, **kwargs):
        """
        Plot Impedance (Fixed units). Real and Imaginary Part
        """
        warn("Unit of x-Axis may not be correct")
        from ..utils import attr_from_unit
        f4h = self._file.impedance(Axis.FAXIS).attrs[attr_from_unit("hz", self._file.version)]
        f4o = self._file.impedance("datagroup").attrs[attr_from_unit("ohm", self._file.version)]
        if f4h == 0:
            warn("Factor4Hertz is zero in datafile using 1.0")
            f4h = np.float64(1.0)
        label = kwargs.pop("label", False)
        if label is not None:
            if label is False:
                label = ""
            else:
                label = label + " "

        @SimplePlotter.plot
        def real(*args, **kwargs):
            return (self._file.impedance(Axis.FAXIS)*f4h,
                   self._file.impedance(Axis.REAL)*f4o, "Frequency in Hz", "Impedance in $\\Omega$")
        if label is not None:
            rlab = label + "Real"
        else:
            rlab = None
        fig = real(*args, label=rlab, **kwargs)
        if 'fig' in kwargs:
            del kwargs['fig']
        @SimplePlotter.plot
        def imag(*args, **kwargs):
            return (self._file.impedance(Axis.FAXIS)*f4h,
                    self._file.impedance(Axis.IMAG)*f4o, "Frequency in Hz", "Impedance in $\\Omega$")
        if label is not None:
            ilab = label + "Imag"
        else:
            ilab = None
        return imag(fig=fig, label=ilab, **kwargs)


class MultiPlot(object):
    """
    Combine multiple files into one plot
    """
    def __init__(self):
        """
        | Creates MultiPlot Instance
        | No Parameters (to add files use add_file)
        """
        self._simple_plotters = []

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
            # self._figure.clear()
            def inner(*args, **kwargs):
                self._figure = plt.figure(tight_layout=True)  # make shure it is only created when actual plotting is wanted
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
        elif object.__hasattr__(self, attr):
            return object.__getattr__(self, attr)
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
        self._data = Data(self._file)
        self._ps_data = {}
        self._eax = None
        self._xax = None
        #self._figure = plt.figure()

    def eax(self):
        if self._eax is None:
            self._eax = self._data.phase_space(Axis.EAXIS, unit='ev')
        return self._eax
    def xax(self):
        if self._xax is None:
            self._xax = self._data.phase_space(Axis.XAXIS, unit='s')
        return self._xax
    def ps_data(self, index):
        if not index in self._ps_data:
            self._ps_data[index] = self._x_to_y(self._data.phase_space(Axis.DATA, unit='cpnblpnes', sub_idx=index))
        return self._ps_data[index]

    def _x_to_y(self, data):
        # return data.T[::-1, :]  # Inovesa phasespace data is in shape [x, y] and imshow needs [y, x]
        # Transpose is enough
        return data.T

    def clone(self):
        """
        | Return a copy of this instance
        | This effectively creates a new object with same file object
        """
        return PhaseSpace(self._file)

    def plot_ps(self, index):
        """
        Plot the phasespace.
        :param index: the index of the dataset (in timeaxis)
        """
        # data = self._file.phase_space[2][index].T[::-1, :] # Transpose because is 90deg wrong
        # data = self._x_to_y(self._file.phase_space(Axis.DATA)[index])
        fig, ax = plt.subplots(1)
        # im = ax.imshow(data)
        xmesh, ymesh = np.meshgrid(np.append(self.xax(), self.xax()[-1]+(self.xax()[-1]-self.xax()[-2])),
                                   np.append(self.eax(), self.eax()[-1]+(self.eax()[-1]-self.eax()[-2])))
        im = ax.pcolormesh(xmesh, ymesh, self.ps_data(index))
        im.set_cmap('inferno')
        ax.set_xlabel("Position in s")
        ax.set_ylabel("Energy in eV")
        return fig, ax, im

    def center_of_mass(self, xax, yax):
        return np.average(xax, weights=yax)

    def phase_space_movie(self, path=None, fr_idx=None, to_idx=None, fps=20, plot_area_width=None, dpi=200):
        """
        Plot a movie of the evolving phasespace
        :param path: Path to a movie file to save to if None: do not save, just return the animation object
        :param fr_idx: Index in the phasespace data to start video
        :param to_idx: Index in the phasespace data to stop video
        :param fps: Frames per second of the output video
        :param plot_area_width: The width in pixel to plot around com. If None will plot full phasespace.
                                (Will plot from com-plot_area_width/2 to com+plot_area_width/2 in space and energy)
        :param dpi: Dots per inch of output video
        :return: animation object
        """
        lb = 0 if fr_idx == None else fr_idx
        ub = len(self._file.phase_space(Axis.DATA)) if to_idx == None else to_idx

        if plot_area_width:
            mbprof = np.mean(self._file.bunch_profile(Axis.DATA)[lb:ub], axis=0)
            meprof = np.mean(self._file.energy_profile(Axis.DATA)[lb:ub], axis=0)
            com_space = self.center_of_mass(range(mbprof.shape[0]), mbprof)
            min_px_space = int(com_space-plot_area_width/2)
            max_px_space = int(com_space+plot_area_width/2)
            com_energy = self.center_of_mass(range(meprof.shape[0]), meprof)
            min_px_energy = int(com_energy-plot_area_width/2)
            max_px_energy = int(com_energy+plot_area_width/2)
        else:
            min_px_space = 0
            max_px_space = self.xax().shape[0]
            min_px_energy = 0
            max_px_energy = self.eax().shape[0]

        ps = self._data.phase_space(Axis.DATA, unit="cpnblpnes")[lb:ub, min_px_space:max_px_space, min_px_energy:max_px_energy]
        fig = plt.figure()
        # fig.subplots_adjust(left=0.17, bottom=0.09, right=1, top=0.96, wspace=None, hspace=None)
        fig.subplots_adjust(left=0.12, bottom=0.09, right=0.8, top=0.96, wspace=None, hspace=None)
        vmin = np.min(ps)
        vmax = np.max(ps)
        xmesh, ymesh = np.meshgrid(
            np.append(self.xax(), self.xax()[-1]+(self.xax()[-1]-self.xax()[-2]))[min_px_space:max_px_space+1]/1e-12,
            np.append(self.eax(), self.eax()[-1]+(self.eax()[-1]-self.eax()[-2]))[min_px_energy:max_px_energy+1]/1e6)

        time_axis = self._data.phase_space(Axis.TIME, unit="ts")[lb:ub]

        style = Style()
        style.apply_to_fig(fig)
        style.update("inverse_ggplot")

        ax = fig.add_subplot(111)
        text = ax.text(0.5, 0.95, "Synchrotron Period: {:.3f} $T_s$".format(time_axis[0]), transform=ax.transAxes, color='white')
        ax.set_xlabel("Position in ps")
        ax.set_ylabel("Energy in MeV")
        im = ax.pcolormesh(xmesh, ymesh, ps[0].T, cmap="inferno")
        im.set_clim((vmin, vmax))
        cax = plt.axes([0.85, 0.1, 0.03, 0.86])
        fig.colorbar(im, cax=cax).set_label("Difference of charge density to mean phase space in C/nEs/nBl")
        if path:
            text.set_animated(True)
            im.set_animated(True)
        style.reapply()

        def do(i):
            text.set_text("Synchrotron Period: {:.3f} $T_s$".format(time_axis[i]))
            im.set_array(ps[i].T.flatten())
            return im,

        if path:
            ani = create_animation(fig, do, range(ub-lb), clear_between=False, fps=fps, blit=False, dpi=dpi, path=path)
        else:
            ani = create_animation(fig, do, range(ub-lb), clear_between=False, fps=fps, blit=False, dpi=dpi)
        return ani

    def microstructure_movie(self, path=None, fr_idx=None, to_idx=None, mean_range=(None, None), fps=20, plot_area_width=None,
                             dpi=200, csr_intensity=False, cmap="RdBu_r", clim=None):
        """
        Plot the difference between the mean phasespace and the current snapshot as video.
        :param path: Path to a movie file to save to if None: do not save, just return the animation object
        :param fr_idx: Index in the phasespace data to start video
        :param to_idx: Index in the phasespace data to stop video
        :param mean_range: The min index and max index to use when calculating the mean of the phasespace
        :param fps: Frames per second of the output video
        :param plot_area_width: The width in pixel to plot around com. If None will plot full phasespace.
                                (Will plot from com-plot_area_width/2 to com+plot_area_width/2 in space and energy)
        :param dpi: Dots per inch of output video
        :param csr_intensity: Also plot CSR intensity and marker of current position
        :param cmap: Colormap to use
        :param clim: Maximum in fraction of global min/max to use as colormap limits
        :return: animation object
        """
        lb = 0 if fr_idx == None else fr_idx
        ub = len(self._file.phase_space(Axis.DATA)) if to_idx == None else to_idx
        lbm = 0 if mean_range[0] is None else mean_range[0]
        ubm = -1 if mean_range[1] is None else mean_range[1]

        if plot_area_width:
            mbprof = np.mean(self._file.bunch_profile(Axis.DATA)[lbm:ubm], axis=0)
            meprof = np.mean(self._file.energy_profile(Axis.DATA)[lbm:ubm], axis=0)
            com_space = self.center_of_mass(range(mbprof.shape[0]), mbprof)
            min_px_space = int(com_space-plot_area_width/2)
            max_px_space = int(com_space+plot_area_width/2)
            com_energy = self.center_of_mass(range(meprof.shape[0]), meprof)
            min_px_energy = int(com_energy-plot_area_width/2)
            max_px_energy = int(com_energy+plot_area_width/2)
        else:
            min_px_space = 0
            max_px_space = self.xax().shape[0]
            min_px_energy = 0
            max_px_energy = self.eax().shape[0]

        ps = self._data.phase_space(Axis.DATA, unit="cpnblpnes")[:, min_px_space:max_px_space, min_px_energy:max_px_energy]
        mean = np.mean(ps[lbm:ubm], axis=0, dtype=np.float64)
        diffs = (ps[lb:ub] - mean)
        fig = plt.figure()
        fig.subplots_adjust(left=0.13, bottom=0.09, right=0.8, top=0.96, wspace=None, hspace=None)
        m = np.max(np.abs([np.min(diffs), np.max(diffs)]))
        if clim:
            m = clim*m
        xmesh, ymesh = np.meshgrid(
            np.append(self.xax(), self.xax()[-1]+(self.xax()[-1]-self.xax()[-2]))[min_px_space:max_px_space+1]/1e-12,
            np.append(self.eax(), self.eax()[-1]+(self.eax()[-1]-self.eax()[-2]))[min_px_energy:max_px_energy+1]/1e6)

        time_axis = self._data.phase_space(Axis.TIME, unit="ts")[lb:ub]

        style = Style()
        style.apply_to_fig(fig)
        style.update("inverse_ggplot")
        style["marker:size"] = 2
        style["line:width"] = 1
        # vline_color = palettes['tango'][1]

        def do_no_csr(i):
            text.set_text("Synchrotron Period: {:.3f} $T_s$".format(time_axis[i]))
            im.set_array(diffs[i].T.flatten())
            return [im]

        def do_csr(i):
            im.set_array(diffs[i].T.flatten())
            p.vertices = np.array([[time_axis[i], csr_min], [time_axis[i], csr_max]])
            return [im, csr_line, vline]

        if csr_intensity:
            csr = self._data.csr_intensity(Axis.DATA, unit="w")[lb:ub]
            _csr_min = np.min(csr)
            _csr_max= np.max(csr)
            _csr_diff = _csr_max - _csr_min
            csr_min = _csr_min - _csr_diff*0.05
            csr_max = _csr_max + _csr_diff*0.05
            from matplotlib.gridspec import GridSpec
            gs = GridSpec(2, 1, height_ratios=[4, 1])
            _cmap = matplotlib.cm.get_cmap(cmap)
            down_color = _cmap(35)

            ax = fig.add_subplot(gs[0, 0])
            ax.set_xlabel("Position in ps")
            ax.set_ylabel("Energy in MeV")

            im = ax.pcolormesh(xmesh, ymesh, diffs[0].T, cmap=cmap)
            im.set_clim((-m, m))
            cax = plt.axes([0.85, 0.1, 0.03, 0.86])
            fig.colorbar(im, cax=cax).set_label("Difference of charge density to mean phase space in C/nEs/nBl")
            ax2 = fig.add_subplot(gs[1, 0])
            csr_line = ax2.plot(time_axis, csr, c=down_color)
            ax2.set_xlabel("Time in $T_s$")
            ax2.set_ylabel("CSR Int. in W")
            ax2.set_ylim(csr_min, csr_max)
            ax2.get_yaxis().get_major_formatter().set_powerlimits((-2, 2))
            vline = ax2.vlines(time_axis[0], csr_min, csr_max, zorder=99)
            p = vline.get_paths()[0]
            plt.subplots_adjust(bottom=0.1, right=0.8, top=0.96, hspace=0.25)
            if path:
                im.set_animated(True)
                vline.set_animated(True)
                csr_line[0].set_animated(True)
            do = do_csr
            style.reapply()
        else:
            ax = fig.add_subplot(111)
            text = ax.text(0.5, 0.95, "Synchrotron Period: {:.3f} $T_s$".format(time_axis[0]), transform=ax.transAxes)
            ax.set_xlabel("Position in ps")
            ax.set_ylabel("Energy in MeV")
            im = ax.pcolormesh(xmesh, ymesh, diffs[0].T, cmap=cmap)
            im.set_clim((-m, m))
            cax = plt.axes([0.85, 0.1, 0.03, 0.86])
            fig.colorbar(im, cax=cax).set_label("Difference of charge density to mean phase space in C/nEs/nBl")
            if path:
                text.set_animated(True)
                im.set_animated(True)
            style.reapply()
            do = do_no_csr

        if path:  # range(len(diffs)) is correct since diffs is only from lb to ub
            ani = create_animation(fig, do, range(len(diffs)), clear_between=False, fps=fps, blit=False, dpi=dpi, path=path)
        else:
            ani = create_animation(fig, do, range(len(diffs)), clear_between=False, fps=fps, blit=False, dpi=dpi)
        return ani


class MultiPhaseSpaceMovie(object):
    """
    | Create Phasespace of multiple Files
    | Useful to check the phasespace over multiple currenst (spectrogram)

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
        ##video stuff - Import here to speed up overall Lisa import time. This will not slow down anything by a lot because create_movie is ony called once per movie (which takes a long time anyway)
        from moviepy.video.io.bindings import mplfig_to_npimage
        from moviepy.video.VideoClip import DataVideoClip
        from moviepy.editor import concatenate_videoclips

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
            clips.append(DataVideoClip(range(len(ps._file.phase_space(Axis.DATA))), lambda dat, ps=ps, clim=clim: dtv(dat, ps, clim), fps=fps))
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
