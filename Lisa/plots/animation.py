import matplotlib.animation as anim
from matplotlib.backend_bases import key_press_handler
import matplotlib
import matplotlib.pyplot as plt
import numbers
import inspect
import numpy as np
import tqdm

def create_animation(figure, frame_generator, frames, fps=None, bitrate=18000, dpi=100, path=None, blit=False,
                     clear_between=False, save_args=None, progress=True, anim_writer="ffmpeg"):
    """
    Create an animation.
    :param figure: The figure to use.
    :param frame_generator: Callable that generates a new frame on figure!
    :param frames: List with index for each frame
    :param fps: The frames per seconds.
    :param bitrate: Bitrate of video
    :param dpi: Dpi of video
    :param path: Path to save the video to. If None does not save.
    :param progress: Show progress bar. If False do not show, if True show one, if integer use as offset for this bar
    """
    plt.ioff()
    if anim_writer is None:
        anim_writer = 'ffmpeg'
    if fps is not None:
        writer = anim.writers[anim_writer](metadata=dict(artist='Lisa'), fps=fps, bitrate=bitrate)
    else:
        writer = anim.writers[anim_writer](metadata=dict(artist='Lisa'), bitrate=bitrate)
    interval = 1/float(fps) * 1000

    params = inspect.signature(frame_generator).parameters

    if clear_between:
        _frame_gen = frame_generator
        def gen(*args ,**kwargs):
            figure.clf()
            figure.canvas.draw()
            return _frame_gen(*args, **kwargs)
        frame_generator = gen

    prog_disable = True if progress is False else False  # test with "is" to ensure it is a boolean
    prog_offset = -1 if not isinstance(progress, int) else progress
    prog_desc = path if path is not None else ""
    progress = tqdm.tqdm(total=len(frames), miniters=1, disable=prog_disable, position=prog_offset, desc=prog_desc)
    if not prog_disable:
        print("\r", end="")  # remove initial print of progressbar
    def generator(*args, **kwargs):
        has_kwargs = any(x.kind == inspect.Parameter.VAR_KEYWORD for x in params.values())
        has_clear = any(x.name == 'clear' for x in params.values())
        if has_clear or has_kwargs:
            kwargs['clear'] = clear_between
        progress.update()
        if args[0] == frames[-1]:
            progress.close()
        return frame_generator(*args, **kwargs)

    ani = anim.FuncAnimation(figure, generator, frames=frames, interval=interval, blit=blit, repeat=False)
    pause = [False]  # list to be mutable to avoid nonlocal to support python2
    def OnKeyPress(event):
        if event.key == 'x' or event.key == ' ':
            if pause[0]:
                progress.write("Resuming")
                ani.event_source.start()
            else:
                progress.write("Pausing")
                ani.event_source.stop()
            pause[0] ^= True
        else:
            key_press_handler(event, figure.canvas, figure.canvas.toolbar)
    figure.canvas.mpl_connect('key_press_event', OnKeyPress)
    if path is not None:
        if save_args is None:
            save_args = {}
        ani.save(path, writer, dpi=dpi, savefig_kwargs=save_args)
    return ani


def data_frame_generator(fig, xdata, ydata, label_only_once=False):
    """
    Generate a frame generator for simple data.
    :param fig: The figure to draw in
    :param xdata: The xdata as iterable
    :param ydata: The ydata as iterable
    :param label_only_once: True to only show x and y tick labels only once (otherwise will be drawn over each other if axis present (not so nice))
    """
    if len(fig.axes) > 0 and not label_only_once:
        print("Warning: An Axis is present, without clearing between frames the x and y axes will be drawn over the original.",
              "Use label_only_once to hide all axes except for the new one.")
    if label_only_once:
        for ax in fig.axes:
            ax.tick_params(axis='both', which='both', bottom=False, top=False, left=False, right=False, labelbottom=False, labeltop=False,
                           labelleft=False, labelright=False)
    axa = fig.add_subplot(111)
    lna, = axa.plot([], [])

    if isinstance(xdata[0], numbers.Number):  # if is 1d (use isinstance of xdata[0] instead of shape to account for non numpy lists)
        def frame_generator(i, clear=False):
            if clear:
                ax = fig.add_subplot(111)
                if not fig._cachedRenderer:
                    fig._cachedRenderer = matplotlib.backends.backend_agg.RendererAgg(640, 480, 100)
                ax.draw(fig._cachedRenderer)
                ax.plot(xdata, ydata[i])
                ax.set_xlim(np.min(xdata), np.max(xdata))
                ax.set_ylim(np.min(ydata[i]), np.max(ydata[i]))
            else:
                ax = axa
                ax.plot(xdata, ydata[i])
            return ax.lines
    else:
        def frame_generator(i, clear=False):
            if clear:
                ax = fig.add_subplot(111)
                if not fig._cachedRenderer:
                    fig._cachedRenderer = matplotlib.backends.backend_agg.RendererAgg(640, 480, 100)
                ax.draw(fig._cachedRenderer)
                ax.plot(xdata[i], ydata[i])
                ax.set_xlim(np.min(xdata[i]), np.max(xdata))
                ax.set_ylim(np.min(ydata[i]), np.max(ydata[i]))
            else:
                ax = axa
                ax.plot(xdata, ydata[i])
            return ax.lines
    return frame_generator
