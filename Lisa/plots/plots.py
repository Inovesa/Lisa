#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
:Author: Patrick Schreiber
"""

import matplotlib.pyplot as plt
import matplotlib

import numpy as np
import glob
from numbers import Number

import sys

import textwrap
from ..internals import config_options
from .animation import create_animation

if config_options.get("use_latex"):
    matplotlib.rc('text', usetex=True)
    matplotlib.rcParams['text.latex.preamble'] = [r'\usepackage{siunitx}']

from ..data import File, Axis
from ..data import Data
from ..plots import Style
from ..internals import lisa_print
from ..data.utils import unit_from_spec, version15_1, attr_from_unit

colors = [(0, 0, 1, 1), (0.8, 0.4, 0, 0.6), (1, 0, 1, 0.6), (0, 1, 1, 0.6), (1, 0, 0, 0.6),
          (0, 1, 0, 0.4)]
trans_value = 0.8

_simple_plotter_plot_methods = []


def warn(x):
    sys.stderr.write("Warning: " + str(x) + "\n")


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
    | Each actual plotting function is decorated using plot or meshPlot. See those for additional
    | parameters to each plot function.
    """
    def __new__(cls, *args, **kwargs):
        # Add video method
        obj = super(SimplePlotter, cls).__new__(cls)
        for func in dir(obj):
            if func.startswith("_"):
                continue
            meshfunc = getattr(obj, func)
            if not hasattr(meshfunc, "mesh"):
                continue

            @cls.video
            def gen_video(self, meshfunc=None, fig=None, how_much=None, nice=False, **kwargs):
                self._file.preload_full(meshfunc.__name__)
                data_func = getattr(self._data, meshfunc.__name__)
                y = data_func(Axis.TIME, unit=None)  # time
                fig.set_size_inches(6.5, 6.5)
                if "zunit" not in kwargs:
                    print("Cannot set min/max if not explicitly set zunit")
                    mi = None
                    ma = None
                else:
                    mi = np.min(data_func(Axis.DATA, unit=kwargs.get("zunit")))
                    ma = np.max(data_func(Axis.DATA, unit=kwargs.get("zunit")))
                    pref = obj._get_metric_prefix([mi, ma])
                    mi /= pref[1]
                    ma /= pref[1]
                number = y.shape[0]
                how_much = how_much if how_much is not None else number
                frames = np.arange(number - how_much, number)

                def up(i):
                    x = meshfunc(i, use_index=True, fig=fig,
                                 label="SyncPeriod: {:0<4}".format(str(y[i])), **kwargs).axes[0]
                    if mi is not None:
                        x.set_ylim(mi - ma * 0.01, ma * 1.05)
                    if nice:
                        fig.current_style.update("inverse_ggplot-dotted")
                    return x.lines
                return fig, up, frames
            setattr(obj, meshfunc.__name__ + "_video",
                    lambda meshfunc=meshfunc, *args, **kwargs: gen_video(obj, meshfunc=meshfunc,
                                                                         **kwargs))
        return obj

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
        Decorator to reuse plotting methods for different data. Calling one of the actual plot
        functions will result in calling this.
        This means the following options are available:

        General Options (always use as keywords):
        :param fig: (optional) the figure to plot in
        :param ax: (optional) the axis to use to plot
        :param label: (optional) the label for this plot (legend)
        :param scale_factor: (optional) a scale factor Note: This does not modify the labels
        :param use_offset: (optional) a bool if one wants an offset on yaxis or not
        :param force_exponential_x: (optional) a bool to force exponential notation on xaxis or not
        :param force_exponential_y: (optional) a bool to force exponential notation on yaxis or not
        :param fft: (optional) a bool to plot fft(data) instead of data or string for method to
                use in numpy.fft
        :param fft_padding: (optional) an integer to specify how much 0 will be padded to the data
                before fft default fft
        :param abs: (optional) a boolean to select if plot absolute values or direct data
        :param plt_args: (optional) dictionary with arguments to the displaying function
        :param x_log: (optional) a boolean to set the x axis to log scale
        :param y_log: (optional) a boolean to set the y axis to log scale
        :param idx_range: (optional) a tuple with minimum and maximum index to plot
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
                ylabel = "FFT(" + ylabel + ")"
                xlabel = "Frequency like (1/(" + xlabel + "))"
                if kwargs.get("fft_padding"):
                    y = np.append([0] * kwargs.get("fft_padding"), y)
                    y = np.append(y, [0] * kwargs.get("fft_padding"))
                if kwargs.get("fft") is True:
                    x = np.fft.fftfreq(x.shape[0] + 2 * kwargs.get("fft_padding", 0), x[1] - x[0])
                    y = np.fft.fft(y)
                else:
                    x = getattr(np.fft,
                                kwargs.get("fft") + "freq")(x.shape[0] + 2 *
                                                            kwargs.get("fft_padding", 0),
                                                            x[1] - x[0])
                    y = getattr(np.fft, kwargs.get("fft"))(y)
            if kwargs.get("abs"):
                y = np.abs(y)
            alpha = None
            if 'alpha' in kwargs.get("plt_args", {}):
                alpha = kwargs.get("plt_args").get("alpha")
                del kwargs.get("plt_args")['alpha']
            if 'label' in kwargs.get("plt_args", {}):
                warn("'label' in plt_args is invalid. Use label in arguments. Will ignore.")
                del kwargs.get("plt_args")['labemporl']
            if hasattr(fig, "num_of_plots"):
                nop = fig.num_of_plots
                fig.num_of_plots += 1
            else:
                nop = 0
                fig.num_of_plots = 1
            if isinstance(kwargs.get("idx_range"), (tuple, list)):
                if len(kwargs.get("idx_range")) != 2:
                    raise ValueError("idx_range has to be a 2-tuple")
                x = x[kwargs.get("idx_range")[0]: kwargs.get("idx_range")[1]]
                y = y[kwargs.get("idx_range")[0]: kwargs.get("idx_range")[1]]
            if "label" in kwargs:
                alpha = ((trans_value if nop > 0 else 1) if alpha is None else alpha)
                ax.plot(x, np.array(y) * scale_factor, label=kwargs["label"], alpha=alpha,
                        **kwargs.get("plt_args", {}))
                ax.legend(loc="best")
            else:
                alpha = ((trans_value if nop > 0 else 1) if alpha is None else alpha)
                ax.plot(x, np.array(y) * scale_factor, alpha=alpha, **kwargs.get("plt_args", {}))
            if xlabel != "" and ax.get_xlabel() != "" and xlabel != ax.get_xlabel():
                xlabel = ax.get_xlabel() + "\n" + xlabel
            if ylabel != "" and ax.get_ylabel() != "" and ylabel != ax.get_ylabel():
                ylabel = ax.get_ylabel() + "\n" + ylabel
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
        decorated.__doc__ = "This method is decorated. See SimplePlotter.plot " \
                            "for additional parameters"
        if func.__doc__ is not None:
            decorated.__doc__ += "\nSpecial Options for this plot:" + textwrap.dedent(func.__doc__)
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
        :param norm: (optional) mpl Norm object or one of ["linear", "log"] to use for pcolormesh
                (default linear)
        :param colormap: (optional) the colormap for pcolormesh to use (default PuBu)
        :param force_bad_to_min: (optional) force bad values (e.g. negative or zero in LogNorm) of
                colorbar to minimum color of colorbar
        :param force_exponential_x: (optional) a bool if one wants to force exponential notation on
                xaxis or not
        :param force_exponential_y: (optional) a bool if one wants to force exponential notation on
                yaxis or not
        :param plt_args: (optional) dictionary with arguments to the displaying function
        :param period: (optional) the period to use. If not given will plot all data as pcolormesh
                (use parameters from plot)
        :param use_index: (optional) Use period as index in data and not synchrotron period
                (default False)
        :param mean_range: (optional) If given plot a normal plot but with data from mean of the
                given range (use parameters from plot)
        :param transpose: (optional) Transpose the 2d Plot (x-axis is time instead of y-axis)
        """
        _simple_plotter_plot_methods.append(func.__name__)

        def decorated(*args, **kwargs):
            period, x, y, z, xlabel, ylabel, zlabel, time_prefix = func(*args, **kwargs)
            if period is not None:
                print_interpol = False
                if kwargs.get("use_index", False):
                    idx = period
                else:
                    if period not in y:
                        lisa_print("Interpolating for usable period (using nearest): ",
                                   end="", debug=False)
                        print_interpol = True
                    if period < 0:
                        period = np.max(y) + period
                    idx = np.argmin(np.abs(np.array(y) - period * 1 / time_prefix[1]))
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
                if isinstance(kwargs['norm'], matplotlib.colors.Normalize):
                    norm = kwargs['norm']
                else:
                    if kwargs['norm'].lower() == "linear":
                        norm = matplotlib.colors.Normalize()
                    elif kwargs['norm'].lower() == "log":
                        norm = matplotlib.colors.LogNorm()
                    else:
                        print("Unknown norm specification, using linear")
                        norm = matplotlib.colors.Normalize()
            else:
                norm = matplotlib.colors.Normalize()
            # warn if values in kwargs and plt_args
            if 'norm' in kwargs.get("plt_args", {}):
                warn("'norm' is already in arguments, duplicate in plt_args, "
                     "will not use norm in plt_args")
                del kwargs.get("plt_args")['norm']
            if 'cmap' in kwargs.get("plt_args", {}):
                warn("'cmap' will be set by this method. use colormap argument "
                     "instead of cmap in plt_args.\n" + "will ignore cmap in plt_args.")
                del kwargs.get("plt_args")['cmap']
            if kwargs.get("transpose", False):
                x, y = y, x
                xlabel, ylabel = ylabel, xlabel
                z = z.T
            pm = ax.pcolormesh(x, y, z, norm=norm, cmap=kwargs.get("colormap", "PuBu"),
                               **kwargs.get("plt_args", {}))
            ax.set_xlabel(xlabel)  # TODO: What?
            ax.set_ylabel(ylabel)
            if kwargs.get("force_bad_to_min", False):
                pm.get_cmap().set_bad((pm.get_cmap()(pm.get_clim()[0])))

            if kwargs.get("force_exponential_x", False):
                ax.get_xaxis().get_major_formatter().set_powerlimits((0, 0))
            if kwargs.get("force_exponential_y", False):
                ax.get_yaxis().get_major_formatter().set_powerlimits((0, 0))
            colorbar = fig.colorbar(pm)
            colorbar.set_label(zlabel)
            fig.cbar = colorbar
            s = Style()
            s.apply_to_fig(fig)
            return fig

        decorated.__name__ = func.__name__
        decorated.__doc__ = "This method is decorated. See SimplePlotter.plot " \
                            "for additional parameters"
        if func.__doc__ is not None:
            decorated.__doc__ += "\nSpecial Options for this plot:" + textwrap.dedent(func.__doc__)
        decorated.mesh = True
        return decorated

    def _unit_and_label(self, kwargs, idx, axis, data, default, label, gen_sub=False):
        if gen_sub:
            d = getattr(self._data, data + "_raw")(idx)
            data_unit = kwargs.get(axis + "unit", default)
            if idx in [Axis.DATA, Axis.XDATA, Axis.YDATA, Axis.IMAG, Axis.REAL]:
                tmp_d = getattr(self._data, data)(idx, unit=data_unit, sub_idx=0)
            else:
                tmp_d = getattr(self._data, data)(idx, unit=data_unit)
            prefix = self._get_metric_prefix(tmp_d)
            del tmp_d

            def unit_function(idx, _data=data, _idx=idx, _unit=data_unit):
                d = getattr(self._data, _data)(_idx, unit=_unit, sub_idx=idx)
                d *= 1 / prefix[1]
                return d
            d.unit_function = unit_function
        else:
            d = getattr(self._data, data)(idx, unit=kwargs.get(axis + "unit", default))
            prefix = self._get_metric_prefix(d)
            d *= 1 / prefix[1]
        lab = label + " in " + prefix[0] + unit_from_spec(kwargs.get(axis + "unit", default))
        return d, lab, prefix

    def _get_metric_prefix(self, data):
        if config_options.get("use_latex"):
            mu = "$\si{\micro}$"
        else:
            mu = "$\mu$"
        metric_prefixes = [("T", 1e12), ("G", 1e9), ("M", 1e6), ("k", 1e3), ("", 1), ("m", 1e-3),
                           (mu, 1e-6), ("n", 1e-9), ("p", 1e-12), ("f", 1e-15)]
        mi = np.min(data)
        mi = 0 if mi < 0 else mi
        ma = np.max(data)
        mean = (mi + ma) / 2
        for prefix in metric_prefixes:  # start with small values
            if prefix[1] <= mean:  # as soon as the smalles prefix is bigger than mean use this
                return prefix
        if mean == 0:
            return "", 1
        elif mean > metric_prefixes[0][1]:
            return metric_prefixes[0]
        else:
            return metric_prefixes[-1]

    @plot
    def energy_spread(self, **kwargs):
        """
        kwargs:
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "eV", "raw"
        """
        x, xlabel, _ = self._unit_and_label(kwargs, Axis.TIME, 'x', 'energy_spread', 'ts', "T")
        y, ylabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'y', 'energy_spread', 'eV',
                                            "Energy Spread")
        return x, y, xlabel, ylabel

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
          * pad_zero: True or False. Pad data to zero to avoid white lines in plot (only considered
                 if period is None or not given)
        """
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) \
            else kwargs.get('period', None)
        x, xlabel, _ = self._unit_and_label(kwargs, Axis.XAXIS, 'x',
                                            'bunch_profile', 's', "Position")
        y, ylabel, time_prefix = self._unit_and_label(kwargs, Axis.TIME, 'y',
                                                      'bunch_profile', 'ts', "T")
        dataunit = kwargs.get("zunit", 'c/s')
        if period is None:  # if no period provided
            z, zlabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'z', 'bunch_profile', dataunit,
                                                "Ch. Dens.")
            if kwargs.get("pad_zero", False):
                z[np.where(z < np.float64(0.0))] = np.float64(1e-100)
        else:
            z, zlabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'z', 'bunch_profile', dataunit,
                                                "Ch. Dens.", gen_sub=True)

        return period, x, y, z, xlabel, ylabel, zlabel, time_prefix

    @meshPlot
    def wake_potential(self, *args, **kwargs):
        """
        | Plot the wake_potential either as line plot or as pcolormesh
        | to plot as line pass either the period as first argument or a keyword argument period
        | Note: if yunit is passed period is in that unit, else in default value.

        kwargs: (first value is default)
          * xunit: possible values: "meters", "seconds", "raw"
          * yunit: possible values: "ts", "seconds", "raw"
          * zunit: possible values: "volt", "raw"
          * pad_zero: True or False. Pad data to zero to avoid white lines in plot
                (only considered if period is None or not given)
        """
        # TODO: Check in what versions of Inovesa this is available
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period',
                                                                                          None)
        x, xlabel, _ = self._unit_and_label(kwargs, Axis.XAXIS, 'x', 'wake_potential', 's', "x")
        y, ylabel, time_prefix = self._unit_and_label(kwargs, Axis.TIME, 'y', 'wake_potential',
                                                      'ts', "T")
        if period is None:  # if no period provided
            z, zlabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'z', 'wake_potential', "volt",
                                                "Wake Potential")
        else:
            z, zlabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'z', 'wake_potential', "volt",
                                                "Wake Potential", gen_sub=True)
        return period, x, y, z, xlabel, ylabel, zlabel, time_prefix

    @plot
    def bunch_length(self, **kwargs):
        """
        kwargs:
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "meters", "secons", "raw"
        """
        x, xlabel, _ = self._unit_and_label(kwargs, Axis.TIME, 'x', 'bunch_length', 'ts', "T")
        y, ylabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'y', 'bunch_length', 'm',
                                            "Bunch Length")
        return x, y, xlabel, ylabel

    @plot
    def csr_intensity(self, **kwargs):
        """
        kwargs:
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "watt", "raw"
        """
        x, xlabel, _ = self._unit_and_label(kwargs, Axis.TIME, 'x', 'csr_intensity', 'ts', "T")
        y, ylabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'y', 'csr_intensity', 'W',
                                            "CSR Intensity")
        return x, y, xlabel, ylabel

    @plot
    def bunch_position(self, **kwargs):
        """
        kwargs: (first value is default)
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "meters", "seconds", "raw"
        """
        x, xlabel, _ = self._unit_and_label(kwargs, Axis.TIME, 'x', 'bunch_position', 'ts', "T")
        y, ylabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'y', 'bunch_position', 'm',
                                            "Bunch Position")
        return x, y, xlabel, ylabel

    @plot
    def bunch_population(self, **kwargs):
        """
        kwargs: (first value is default)
          * xunit: possible values: "ts", "seconds", "raw"
          * yunit: possible values: "meters", "seconds", "raw"
        """
        x, xlabel, _ = self._unit_and_label(kwargs, Axis.TIME, 'x', 'bunch_population', 'ts', "T")
        y, ylabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'y', 'bunch_population', 'c',
                                            "Bunch Population")
        return x, y, xlabel, ylabel

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
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period',
                                                                                          None)
        x, xlabel, _ = self._unit_and_label(kwargs, Axis.FAXIS, 'x', 'csr_spectrum', 'Hz',
                                            "Frequency")
        y, ylabel, time_prefix = self._unit_and_label(kwargs, Axis.TIME, 'y', 'csr_spectrum',
                                                      'ts', "T")
        if period is None:  # if no period provided
            z, zlabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'z', 'csr_spectrum', 'wphz',
                                                "Power")
            if kwargs.get("pad_zero", False):
                z[np.where(z < np.float64(0.0))] = np.float64(1e-100)
        else:
            z, zlabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'z', 'csr_spectrum', 'wphz',
                                                "Power", gen_sub=True)
        return period, x, y, z, xlabel, ylabel, zlabel, time_prefix

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
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period',
                                                                                          None)
        x, xlabel, _ = self._unit_and_label(kwargs, Axis.EAXIS, 'x', 'energy_profile', 'eV',
                                            "Energy Deviation")
        y, ylabel, time_prefix = self._unit_and_label(kwargs, Axis.TIME, 'y', 'energy_profile',
                                                      'ts', "T")
        dataunit = "c" if self._file.version < version15_1 else "cpnes"
        if period is None:  # if no period provided
            z, zlabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'z', 'energy_profile',
                                                dataunit, "Population")
            if kwargs.get("pad_zero", False):
                z[np.where(z < np.float64(0.0))] = np.float64(1e-100)
        else:
            z, zlabel, _ = self._unit_and_label(kwargs, Axis.DATA, 'z', 'energy_profile',
                                                dataunit, "Population", gen_sub=True)
        return period, x, y, z, xlabel, ylabel, zlabel, time_prefix

    def impedance(self, *args, **kwargs):
        """
        Plot Impedance (Fixed units). Real and Imaginary Part
        """
        warn("Unit of x-Axis may not be correct")
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

        x = self._file.impedance(Axis.FAXIS) * f4h
        yreal = self._file.impedance(Axis.REAL) * f4o
        yimag = self._file.impedance(Axis.IMAG) * f4o
        xprefix = self._get_metric_prefix(x)
        # check for one is const 0
        if np.min(yreal) == np.max(yreal) == 0:
            prefix_data = yimag
        elif np.min(yimag) == np.max(yimag) == 0:
            prefix_data = yreal
        else:
            prefix_data = [np.mean(np.min([yreal, yimag])), np.mean(np.max([yreal, yimag]))]
        yprefix = self._get_metric_prefix(prefix_data)

        x /= xprefix[1]
        yreal /= yprefix[1]
        yimag /= yprefix[1]

        @SimplePlotter.plot
        def real(*args, **kwargs):
            return x, yreal, "Frequency in " + xprefix[0] + \
                "Hz", "Impedance in " + yprefix[0] + "$\\Omega$"

        if label is not None:
            rlab = label + "Real"
        else:
            rlab = None
        fig = real(*args, label=rlab, **kwargs)
        if 'fig' in kwargs:
            del kwargs['fig']

        @SimplePlotter.plot
        def imag(*args, **kwargs):
            return x, yimag, "Frequency in " + xprefix[0] + "Hz", \
                   "Impedance in " + yprefix[0] + "$\\Omega$"

        if label is not None:
            ilab = label + "Imag"
        else:
            ilab = None
        return imag(fig=fig, label=ilab, **kwargs)

    def video(func):
        def wrapped(self, **kwargs):
            """
            Create a video
            :param kwargs: passed to wrapped function except for "outpath", "anim_writer", "fps", "
                    dpi"
            :return:
            """
            fig, ax = plt.subplots()
            kwargs.setdefault('fig', fig)
            kwargs.setdefault('ax', ax)
            outpath = kwargs.pop("outpath", None)
            fps = kwargs.pop("fps", 20)
            dpi = kwargs.pop("dpi", 200)
            anim_writer = kwargs.pop("anim_writer", None)
            fig, update_func, frames = func(self, **kwargs)
            fig.tight_layout()
            ani = create_animation(fig, update_func, frames, clear_between=True, fps=fps,
                                   blit=False, path=outpath, dpi=dpi, anim_writer=anim_writer)
            return ani
        return wrapped


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
                warn("MultiPlot." + attr + " called without files to plot.")

            warn_no_file.__doc__ = "Dummy Method. Retry when files are added."
            warn_no_file.__name__ = attr
            return warn_no_file
        if hasattr(self._simple_plotters[0][0], attr):
            def inner(*args, **kwargs):
                self._figure = plt.figure(tight_layout=True)
                kwargs["fig"] = self._figure
                for sp in self._simple_plotters:
                    if sp[1] is not None:
                        kwargs["label"] = sp[1]
                    getattr(sp[0], attr)(*args, **kwargs)
                return self._figure
            inner.__name__ = attr
            inner.__doc__ = "MultiPlot." + attr + " will override 'fig' kwarg. \n" \
                            "If 'label' was passed to add_file " +\
                            "'label' in kwarg will be overriden with that value for the " \
                            "corresponding file.\n" + \
                            "\nDelegated Options from SimplePlotter:\n" + \
                            getattr(self._simple_plotters[0][0], attr).__doc__
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

    def eax(self):
        if self._eax is None:
            self._eax = self._data.phase_space(Axis.EAXIS, unit='ev')
        return self._eax

    def xax(self):
        if self._xax is None:
            self._xax = self._data.phase_space(Axis.XAXIS, unit='s')
        return self._xax

    def ps_data(self, index):
        if index not in self._ps_data:
            self._ps_data[index] = self._x_to_y(self._data.phase_space(Axis.DATA, unit='cpnblpnes',
                                                                       sub_idx=index))
        return self._ps_data[index]

    def _x_to_y(self, data):
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
        fig, ax = plt.subplots(1)
        xmesh, ymesh = np.meshgrid(np.append(self.xax(),
                                             self.xax()[-1] + (self.xax()[-1] - self.xax()[-2])),
                                   np.append(self.eax(),
                                             self.eax()[-1] + (self.eax()[-1] - self.eax()[-2])))
        im = ax.pcolormesh(xmesh, ymesh, self.ps_data(index))
        im.set_cmap('inferno')
        ax.set_xlabel("Position in s")
        ax.set_ylabel("Energy Deviation in eV")
        return fig, ax, im

    def center_of_mass(self, xax, yax):
        return np.average(xax, weights=yax)

    def phase_space_movie(self, path=None, fr_idx=None, to_idx=None, fps=20, plot_area_width=None,
                         dpi=200, csr_intensity=False, bunch_profile=False, cmap="inferno",
                          clim=None, extract_slice=None, **kwargs):
        """
        Plot a movie of the evolving phasespace
        :param path: Path to a movie file to save to if None: do not save, just return the
                animation object
        :param fr_idx: Index in the phasespace data to start video
        :param to_idx: Index in the phasespace data to stop video
        :param fps: Frames per second of the output video
        :param plot_area_width: The width in pixel to plot around com. If None will plot full
                phasespace. (Will plot from com-plot_area_width/2 to com+plot_area_width/2
                in space and energy)
        :param dpi: Dots per inch of output video
        :param csr_intensity: Also plot CSR intensity and marker of current position
        :param bunch_profile: Also plot the bunch profile for current synchrotron period
        :param cmap: Colormap to use
        :param clim: Maximum in fraction of global min/max to use as colormap limits
        :param extract_slice: Extract a slice and do no movie, just return the plot. This is a
                string in format idx:int for an actual slice or ts:float for a specific synchrotron
                period (or the nearest value). Or it is an integer for a slice index
                (same as idx:int)
        :param **kwargs: Keyword arguments passed to create_animation
        :return: animation object
        """

        lb, ub, lbm, ubm, min_px_space, max_px_space, min_px_energy, max_px_energy = \
            self._gen_bounds(fr_idx, to_idx, plot_area_width)

        ps = self._data.phase_space(Axis.DATA, unit="cpnblpnes")[lb:ub, min_px_space:max_px_space,
                                                                 min_px_energy:max_px_energy]
        return self._gen_ps_movie(ps, min_px_space, max_px_space, min_px_energy, max_px_energy,
                                  clim, lb, ub, bunch_profile, csr_intensity, cmap, extract_slice,
                                  fps, path, dpi, **kwargs)

    def microstructure_movie(self, path=None, fr_idx=None, to_idx=None, mean_range=(None, None),
                             fps=20, plot_area_width=None, dpi=200, csr_intensity=False,
                             bunch_profile=False, cmap="RdBu_r", clim=None,
                             extract_slice=None, **kwargs):
        """
        Plot the difference between the mean phasespace and the current snapshot as video.
        :param path: Path to a movie file to save to if None: do not save, just return the animation
                object
        :param fr_idx: Index in the phasespace data to start video
        :param to_idx: Index in the phasespace data to stop video
        :param mean_range: The min index and max index to use when calculating the mean of the
                phasespace
        :param fps: Frames per second of the output video
        :param plot_area_width: The width in pixel to plot around com. If None will plot full
                phasespace.
                (Will plot from com-plot_area_width/2 to com+plot_area_width/2 in space and energy)
        :param dpi: Dots per inch of output video
        :param csr_intensity: Also plot CSR intensity and marker of current position
        :param bunch_profile: Also plot the bunch profile for current synchrotron period
        :param cmap: Colormap to use
        :param clim: Maximum in fraction of global min/max to use as colormap limits
        :param extract_slice: Extract a slice and do no movie, just return the plot. This is a
                string in format idx:int for an actual slice or ts:float for a specific synchrotron
                period (or the nearest value). Or it is an integer for a slice index
                (same as idx:int)
        :param **kwargs: Keyword arguments passed to create_animation
        :return: animation object
        """

        lb, ub, lbm, ubm, min_px_space, max_px_space, min_px_energy, max_px_energy = \
            self._gen_bounds(fr_idx, to_idx, plot_area_width, mean_range)
        ps = self._data.phase_space(Axis.DATA, unit="cpnblpnes")[:, min_px_space:max_px_space,
                                                                 min_px_energy:max_px_energy]
        mean = np.mean(ps[lbm:ubm], axis=0, dtype=np.float64)
        diffs = (ps[lb:ub] - mean)
        return self._gen_ps_movie(diffs, min_px_space, max_px_space, min_px_energy, max_px_energy,
                                  clim, lb, ub, bunch_profile, csr_intensity, cmap, extract_slice,
                                  fps, path, dpi, symmetric=True, **kwargs)

    def _gen_bounds(self, fr_idx, to_idx, plot_area_width, mean_range=None):
        lb = 0 if fr_idx is None else fr_idx
        ub = len(self._file.phase_space(Axis.DATA)) if to_idx is None else to_idx
        if mean_range is not None:
            lbm = 0 if mean_range[0] is None else mean_range[0]
            ubm = -1 if mean_range[1] is None else mean_range[1]
        else:
            lbm = lb
            ubm = ub

        if plot_area_width:
            mbprof = np.mean(self._file.bunch_profile(Axis.DATA)[lbm:ubm], axis=0)
            meprof = np.mean(self._file.energy_profile(Axis.DATA)[lbm:ubm], axis=0)
            com_space = self.center_of_mass(range(mbprof.shape[0]), mbprof)
            min_px_space = max(int(com_space - plot_area_width / 2), 0)
            max_px_space = min(int(com_space + plot_area_width / 2), mbprof.shape[0])
            com_energy = self.center_of_mass(range(meprof.shape[0]), meprof)
            min_px_energy = max(int(com_energy - plot_area_width / 2), 0)
            max_px_energy = min(int(com_energy + plot_area_width / 2), meprof.shape[0])
        else:
            min_px_space = 0
            max_px_space = self.xax().shape[0]
            min_px_energy = 0
            max_px_energy = self.eax().shape[0]
        return lb, ub, lbm, ubm, min_px_space, max_px_space, min_px_energy, max_px_energy

    def _gen_ps_movie(self, data, min_px_space, max_px_space, min_px_energy, max_px_energy,
                      clim, lb, ub, bunch_profile, csr_intensity, cmap, extract_slice,
                      fps, path, dpi, symmetric=False, **kwargs):

        def forceAspect(ax, aspect=1):
            ax.set_aspect(np.abs((ax.get_xlim()[1] - ax.get_xlim()[0]) /
                                 (ax.get_ylim()[1] - ax.get_ylim()[0])) / aspect)

        fig = plt.figure()
        fig.set_size_inches(7, 7)
        ma = np.max(np.abs([np.min(data), np.max(data)]))
        if clim:
            ma = clim * ma
        mi = -ma if symmetric else 0
        xmesh, ymesh = np.meshgrid(
            np.append(self.xax(), self.xax()[-1] + (self.xax()[-1] - self.xax()[-2]))[
                                                    min_px_space:max_px_space + 1] / 1e-12,
            np.append(self.eax(), self.eax()[-1] + (self.eax()[-1] - self.eax()[-2]))[
                                                    min_px_energy:max_px_energy + 1] / 1e6)

        time_axis = self._data.phase_space(Axis.TIME, unit="ts")[lb:ub]

        style = Style()
        style.apply_to_fig(fig)
        style.update("inverse_ggplot")
        style["marker:size"] = 2
        style["line:width"] = 1

        def do_ms(i):
            text.set_text("Synchrotron Period: {:.3f} $T_s$".format(time_axis[i]))
            im.set_array(data[i].T.flatten())
            return [im]

        dos = [do_ms]

        def do_csr(i):
            if bunch_profile and csr_intensity:
                p.vertices = np.array([[csr_min, time_axis[i]], [csr_max, time_axis[i]]])
            else:
                p.vertices = np.array([[time_axis[i], csr_min], [time_axis[i], csr_max]])
            return [csr_line, vline]

        def do_bp(i):
            bp_line.set_ydata(bp[i])
            return [bp_line]

        def do(i):
            r = []
            for d in dos:
                r.extend(d(i))
            return r

        if csr_intensity or bunch_profile and not (csr_intensity and bunch_profile):
            from matplotlib.gridspec import GridSpec
            gs = GridSpec(2, 1, height_ratios=[5, 1])
            gs_csr = gs_bl = gs[1, 0]
            plt.subplots_adjust(bottom=0.1, right=0.75, top=0.96, hspace=0.18)

        if csr_intensity and bunch_profile:
            left = 0.08
            right = 0.8
            bottom = 0.07
            top = 0.92
            plt.subplots_adjust(left=left, bottom=bottom, right=right, top=top, hspace=0.03,
                                wspace=0.03)
            from matplotlib.gridspec import GridSpec
            gs = GridSpec(2, 2, height_ratios=[5, 1], width_ratios=[5, 1])
            gs_csr = gs[0, 1]
            gs_bl = gs[1, 0]
            fig.set_size_inches(7 * (top - bottom) / (right - left), 7)

        if csr_intensity:
            csr = self._data.csr_intensity(Axis.DATA, unit="w")[lb:ub]
            _csr_min = np.min(csr)
            _csr_max = np.max(csr)
            _csr_diff = _csr_max - _csr_min
            csr_min = _csr_min - _csr_diff * 0.05
            csr_max = _csr_max + _csr_diff * 0.05

            _cmap = matplotlib.cm.get_cmap(cmap)
            down_color = _cmap(35)
            ax2 = fig.add_subplot(gs_csr)
            if bunch_profile:
                csr_line = ax2.plot(csr, time_axis, c=down_color)
                ax2.set_ylabel("Time in $T_s$", rotation=270, va='top', ha='left', labelpad=12)
                ax2.set_xlabel("CSR Int. in W")
                ax2.set_xlim(csr_min, csr_max)
                ax2.get_xaxis().get_major_formatter().set_powerlimits((-2, 2))
                vline = ax2.hlines(time_axis[0], csr_min, csr_max, zorder=99)
                p = vline.get_paths()[0]
                ax2.yaxis.tick_right()
                ax2.yaxis.set_label_position('right')
            else:
                csr_line = ax2.plot(time_axis, csr, c=down_color)
                ax2.set_xlabel("Time in $T_s$")
                ax2.set_ylabel("CSR Int. in W")
                ax2.set_ylim(csr_min, csr_max)
                ax2.get_yaxis().get_major_formatter().set_powerlimits((-2, 2))
                vline = ax2.vlines(time_axis[0], csr_min, csr_max, zorder=99)
                p = vline.get_paths()[0]
            dos.append(do_csr)
            if path:
                vline.set_animated(True)
                csr_line[0].set_animated(True)

        if bunch_profile:
            bp = self._data.bunch_profile(Axis.DATA, unit="c/s")[lb:ub]
            bpax = self._data.bunch_profile(Axis.XAXIS, unit='s') * 1e12
            _bp_min = np.min(bp)
            _bp_max = np.max(bp)
            _bp_diff = _bp_max - _bp_min
            bp_min = _bp_min - _bp_diff * 0.05
            bp_max = _bp_max + _bp_diff * 0.05
            _cmap = matplotlib.cm.get_cmap(cmap)
            down_color = _cmap(35)
            ax3 = fig.add_subplot(gs_bl)  # hm is 1 if only bunch_profile else 2
            bp_line, = ax3.plot(bpax, bp[0], c=down_color)
            ax3.set_xlabel("Position in ps")
            ax3.set_ylabel("Ch. Dens. in c/s")
            ax3.set_ylim(bp_min, bp_max)
            ax3.get_yaxis().get_major_formatter().set_powerlimits((-2, 2))
            dos.append(do_bp)
            if path:
                bp_line.set_animated(True)

        if bunch_profile or csr_intensity:
            ax = fig.add_subplot(gs[0, 0])
            ax.set_xlabel("Position in ps")
            ax.set_ylabel("Energy Deviation in MeV")
            bb = ax.get_position()
            if bunch_profile and csr_intensity:
                ax.xaxis.tick_top()
                ax.xaxis.set_label_position('top')
                cax = plt.axes([0.88, bb.min[1], 0.03, bb.height])
            else:
                cax = plt.axes([0.84, bb.min[1], 0.03, bb.height])
            im = ax.pcolormesh(xmesh, ymesh, data[0].T, cmap=cmap)
            im.set_clim((mi, ma))
            forceAspect(ax)
            fig.colorbar(im, cax=cax).set_label(
                "Difference of charge density to mean phase space in C/nEs/nBl",
                rotation=270, labelpad=12)

            text = ax.text(0.5, 0.95, "Synchrotron Period: {:.3f} $T_s$".format(time_axis[0]),
                           transform=ax.transAxes)
            if path:
                text.set_animated(True)
                im.set_animated(True)

            style.reapply()
        else:
            fig.subplots_adjust(left=0.13, bottom=0.09, right=0.8, top=0.96, wspace=None,
                                hspace=None)
            ax = fig.add_subplot(111)
            text = ax.text(0.5, 0.95, "Synchrotron Period: {:.3f} $T_s$".format(time_axis[0]),
                           transform=ax.transAxes)
            ax.set_xlabel("Position in ps")
            ax.set_ylabel("Energy Deviation in MeV")
            im = ax.pcolormesh(xmesh, ymesh, data[0].T, cmap=cmap)
            im.set_clim((mi, ma))
            cax = plt.axes([0.85, 0.1, 0.03, 0.86])
            fig.colorbar(im, cax=cax).set_label(
                "Difference of charge density to mean phase space in C/nEs/nBl"
            )
            fig.set_size_inches(7 * 1 / 0.85, 7)
            if path:
                text.set_animated(True)
                im.set_animated(True)
            style.reapply()

        if extract_slice:
            if isinstance(extract_slice, str):
                if extract_slice.startswith("idx:"):
                    id = range(len(data))[int(extract_slice[4:])]
                elif extract_slice.startswith("ts:"):
                    id = np.argmin(np.abs(time_axis - float(extract_slice[3:])))
                else:
                    raise ValueError("extract_slice in wrong format")
            else:
                id = int(extract_slice)
            do(id)
            return fig
        elif path:  # range(len(data)) is correct since data is only from lb to ub
            sa = kwargs.setdefault("save_args", {})
            sa['pad_inches'] = 0
            ani = create_animation(fig, do, range(len(data)), clear_between=False, fps=fps,
                                   blit=False, dpi=dpi, path=path, **kwargs)
        else:
            ani = create_animation(fig, do, range(len(data)), clear_between=False, fps=fps,
                                   blit=False, dpi=dpi, **kwargs)
        return ani


class MultiPhaseSpaceMovie(object):
    """
    | Create Phasespace of multiple Files
    | Useful to check the phasespace over multiple currenst (spectrogram)

    """
    def __init__(self, path):
        self._path = path

    def _get_current_from_cfg(self, filename):
        with open(filename + ".cfg", 'r') as f:
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
        :param autorescale(=False): if True will autorescale each frame (will not make sense if
                you want to compare)
        :return: True if file produced, moviepy video instance if None as filename was given
        """
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
        for file in glob.glob(self._path + "/*.h5"):
            files.append((self._get_current_from_cfg(file), file))
        files.sort(key=lambda f: f[0], reverse=True)  # make sure it is sorted by the first entry
        clim = None
        for file in files:
            ps = PhaseSpace(file[1])
            if autorescale and clim is None:
                clim = ps.plot_ps(0)[2].get_clim()
            clips.append(DataVideoClip(range(len(ps._file.phase_space(Axis.DATA))),
                                       lambda dat, ps=ps, clim=clim: dtv(dat, ps, clim), fps=fps))
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
