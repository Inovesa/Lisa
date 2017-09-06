import matplotlib.animation as anim
from matplotlib.backend_bases import key_press_handler
import matplotlib.pyplot as plt
import numbers
import inspect
import numpy as np

def create_animation(figure, frame_generator, frames, fps=None, bitrate=18000, dpi=100, path=None, blit=False, clear_between=False, save_args=None):
    """
    Create an animation.
    :param figure: The figure to use.
    :param frame_generator: Callable that generates a new frame on figure!
    :param frames: List with index for each frame
    :param fps: The frames per seconds.
    :param bitrate: Bitrate of video
    :param dpi: Dpi of video
    :param path: Path to save the video to. If None does not save.
    """
    plt.ioff()
    if fps is not None:
        writer = anim.writers['ffmpeg'](metadata=dict(artist='Lisa'), fps=fps, bitrate=bitrate)
    else:
        writer = anim.writers['ffmpeg'](metadata=dict(artist='Lisa'), bitrate=bitrate)
    interval = 1/float(fps) * 1000

    params = inspect.signature(frame_generator).parameters

    if clear_between:
        _frame_gen = frame_generator
        def gen(*args ,**kwargs):
            figure.clf()
            return _frame_gen(*args, **kwargs)
        frame_generator = gen

    import time
    first_time = time.time()
    eta = [0]
    import sys
    try:
        from blhelpers.debug import BeautifulPrinter
        b = BeautifulPrinter(False)
        def perc(p):
            if p != 100:
                dt = time.time() - first_time
                if eta[0] == 0:
                    if p != 0:
                        eta[0] = 100*dt/p
                else:
                    eta[0] = (eta[0] + 100*dt/p)/2
                b.mPercent(p)
                sys.stdout.write(" eta: {:.2f}s/{:.2f}s".format(dt, eta[0]))
                sys.stdout.flush()
    except ImportError:
        def perc(p):

            dt = time.time() - first_time
            if eta[0] == 0:
                if p != 0:
                    eta[0] = 100*dt/p
            else:
                eta[0] = (eta[0] + 100*dt/p)/2
            sys.stdout.write('\r')
            sys.stdout.write("[{0}{1}] {2:.2f}%".format('='*(int(p)-1)+'>', ' '*(100-int(p)), round(p, 2)))
            sys.stdout.write(" eta: {:.2f}s/{:.2f}s".format(dt, eta[0]))
            sys.stdout.flush()

    current_index = 0
    def generator(*args, **kwargs):
        has_kwargs = any(x.kind == inspect.Parameter.VAR_KEYWORD for x in params.values())
        has_clear = any(x.name == 'clear' for x in params.values())
        if has_clear or has_kwargs:
            kwargs['clear'] = clear_between
        nonlocal current_index
        current_index += 1
        perc(current_index/len(frames)*100)
        return frame_generator(*args, **kwargs)

    ani = anim.FuncAnimation(figure, generator, frames=frames, interval=interval, blit=blit, repeat=False)
    pause = False
    def OnKeyPress(event):
        if event.key == 'x' or event.key == ' ':
            nonlocal pause
            if pause:
                print("Resuming")
                ani.event_source.start()
            else:
                print("Pausing")
                ani.event_source.stop()
            pause ^= True
        else:
            key_press_handler(event, figure.canvas, figure.canvas.toolbar)
    figure.canvas.mpl_connect('key_press_event', OnKeyPress)
    if path is not None:
        if save_args is None:
            save_args = {}
        ani.save(path, writer, dpi=dpi, savefig_kwargs=save_args)
    perc(100)
    print()
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
                ln = ax.plot(xdata, ydata[i])
                return ln,
            else:
                nonlocal lna, axa
                lna.set_data(xdata, ydata[i])
                axa.set_xlim(np.min(xdata), np.max(xdata))
                axa.set_ylim(np.min(ydata[i]), np.max(ydata[i]))
                return axa,
    else:
        def frame_generator(i, clear=False):
            if clear:
                ax = fig.add_subplot(111)
                ln = ax.plot(xdata[i], ydata[i])
                return ln,
            else:
                nonlocal lna, axa
                lna.set_data(xdata[i], ydata[i])
                axa.set_xlim(np.min(xdata[i]), np.max(xdata[i]))
                axa.set_ylim(np.min(ydata[i]), np.max(ydata[i]))
                return axa,
    return frame_generator
