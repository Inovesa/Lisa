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
from warnings import warn

##video stuff
from moviepy.video.io.bindings import mplfig_to_npimage
from moviepy.video.VideoClip import DataVideoClip
from moviepy.editor import concatenate_videoclips

from ..file import File
from .config import Style

colors = [(0, 0, 1, 1), (0.8, 0.4, 0, 0.6), (1, 0, 1, 0.6), (0, 1, 1, 0.6), (1, 0, 0, 0.6),
          (0, 1, 0, 0.4)]
trans_value = 0.8

_simple_plotter_plot_methods = []

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
    def __init__(self, filename):
        """
        Initialise a Simple Plotter instance
        :param filename: The file name of this Plotter
        """
        self._file = File(filename)
        self.current = self._file.parameters["BunchCurrent"]
        
    def plot(func):
        """
        Decorator to reuse plotting methods for different data
        """
        _simple_plotter_plot_methods.append(func.__name__)
        def decorated(*args, **kwargs):
            """
            :param fig: (optional) the figure to plot in
            :param label: (optional) the label for this plot (legend)
            """
            scale_factor = kwargs["scale_factor"] if "scale_factor" in kwargs else 1.
            if ("fig" in kwargs and isinstance(kwargs["fig"], plt.Figure)):
                fig = kwargs["fig"]
                ax = fig.add_subplot(111)
            else:
                fig = plt.figure()
                ax = fig.add_subplot(111)
                kwargs["axes"] = ax
            x, y, xlabel, ylabel = func(*args, **kwargs) # arguments contain self object
            if(hasattr(fig, "num_of_plots")):   
                nop = fig.num_of_plots
                fig.num_of_plots += 1
            else:
                nop = 0
                fig.num_of_plots = 1
            if "label" in kwargs:
                ax.plot(x, np.array(y)*scale_factor, label=kwargs["label"], alpha=(trans_value if nop > 0 else 1))
                ax.legend(loc="best")
            else:
                ax.plot(x, np.array(y)*scale_factor, alpha=(trans_value if nop > 0 else 1))
            if(xlabel != "" and ax.get_xlabel()!="" and xlabel!=ax.get_xlabel()):
                xlabel = ax.get_xlabel()+"\n"+xlabel
            if(ylabel != "" and ax.get_ylabel()!="" and ylabel!=ax.get_ylabel()):
                ylabel = ax.get_ylabel()+"\n"+ylabel
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            s = Style()
            s.apply_to_fig(fig)
            return fig
        return decorated

    def meshPlot(func):
        """
        Decorator to reuse plotting methods and to unify colormesh plots and normal line plots
        """
        def decorated(*args, **kwargs):
            """
            :param fig: (optional) the figure to plot in
            :param label: (optional) the label for this plot (legend) (if line plot)
            :param norm: (optional) the norm to use if pcolormesh (default LogNorm)
            """
            period, x, y, z, xlabel, ylabel = func(*args, **kwargs)
            if period is not None:
                if period not in y:
                    print("Interpolating for usable period (using nearest): ",end="")
                idx = np.argmin(np.abs(np.array(y)-period))
                if period not in y:
                    print(y[idx])
                @SimplePlotter.plot
                def dummy(*args, **kwargs):
                    return(x, z[idx], "", "") # TODO: Labels
                return dummy(**kwargs)

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
            pm = ax.pcolormesh(x, y, z, norm=norm)
            ax.set_xlabel(xlabel)  # TODO: What?
            ax.set_ylabel(ylabel)
            s = Style()
            s.apply_to_fig(fig)
            return fig
        return decorated


        
    @plot
    def energy_spread(self, **kwargs):
        return(self._file.energy_spread[0], self._file.energy_spread[1], 
               "T in # Synchrotron Periods", "Energy Spread") # TODO: Unit

    @meshPlot
    def bunch_profile(self, *args, **kwargs):
        """
        Plot the bunch_profile either as line plot or as pcolormesh
        to plot as line pass either the period as first argument or a keyword argument period
        """
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period', None)
        return period, self._file.bunch_profile[0], self._file.bunch_profile[1], self._file.bunch_profile[2], "", ""  # TODO: Labels
    
               
    @plot
    def bunch_length(self, **kwargs):
        return (self._file.bunch_length[0], self._file.bunch_length[1],
                "T in # Synchrotron Periods", "Bunch Length") # TODO: Unit
                
    @plot
    def csr_intensity(self, **kwargs):
        return (self._file.csr_intensity[0], self._file.csr_intensity[1],
                "T in # Synchrotron Periods", "CSR Intensity") # TODO: Unit
                
    @plot
    def bunch_position(self, **kwargs):
        return (self._file.bunch_position[0], self._file.bunch_position[1],
                "T in # Synchrotron Periods", "Bunch Position") # TODO: Unit
    @plot
    def bunch_population(self, **kwargs):
        return (self._file.bunch_population[0], self._file.bunch_population[1],
                "T in # Synchrotron Periods", "Bunch Population") # TODO: Unit

    @meshPlot
    def csr_spectrum(self, *args, **kwargs):
        """
        Plot the csr_spectrum either as line plot or as pcolormesh
        to plot as line pass either the period as first argument or a keyword argument period
        """
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period', None)
        return period, self._file.csr_spectrum[1], self._file.csr_spectrum[0], self._file.csr_spectrum[2], "", ""  # TODO: Labels

    @meshPlot
    def energy_profile(self, *args, **kwargs):
        """
        Plot the energy_profile either as line plot or as pcolormesh
        to plot as line pass either the period as first argument or a keyword argument period
        """
        period = args[0] if len(args) > 0 and isinstance(args[0], Number) else kwargs.get('period', None)
        return period, self._file.energy_profile[0], self._file.energy_profile[1], self._file.energy_profile[2], "", ""  # TODO: Labels

    def impedance(self, *args, **kwargs):
        warn("Unit of x-Axis may not be correct")
        @SimplePlotter.plot
        def real(*args, **kwargs):
            return self._file.impedance[0], self._file.impedance[1], "Frequency in Hz", "Impedance in k$\\Omega$"
        fig = real(*args, label="Real", **kwargs)
        @SimplePlotter.plot
        def imag(*args, **kwargs):
            return self._file.impedance[0], self._file.impedance[2], "Frequency in Hz", "Impedance in k$\\Omega$"
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
        self._figure = plt.figure()
        
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
            def do_nothing():
                pass
            return  do_nothing # Return or do something like raise an exception?
        if hasattr(self._simple_plotters[0][0], attr):
            self._figure.clear()
            def inner(*args, **kwargs):
                kwargs["fig"] = self._figure
                for sp in self._simple_plotters:
                    if sp[1] != None:
                        kwargs["label"] = sp[1]
                    getattr(sp[0], attr)(*args, **kwargs)
                return self._figure
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
            
