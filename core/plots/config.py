import matplotlib as mpl
import matplotlib.pyplot as plt
from warnings import warn

selectors = {'spine': [['top', 'bottom', 'right', 'left'], ['color']],
             'label': [['x', 'y'], ['color', 'fontsize', 'fontfamily']],
             'ticklabels': [['x', 'y'], ['color', 'fontsize', 'fontfamily']],
             'ticks': [['x', 'y'], ['color', 'below', 'direction']],
             'grid': [[], ['color', 'linewidth', 'dashes', 'linestyle', 'visible', 'style']],
             'face': [[], ['color']],
             'legend': [[], ['fontfamily', 'fontsize', 'color']]}

class Alias:
    """
    Alias to another method
    """
    def __init__(self, sel, attr):
        """
        sel is the selector and attr the attribute of the target
        """
        self.sel = sel
        self.attr = attr
    def __call__(self, axes, what, value):
        methods[self.sel][self.attr](axes, what, value)

methods = {'spine': {'color': lambda ax, w, v: ax.spines[w].set_color(v)},
           'ticklabels': {'color': lambda ax, w, v: [i.set_color(v) for i in getattr(ax, ''.join(['get_', w, 'ticklabels']))()],
                          'fontsize': lambda ax, w, v: [i.set_fontsize(v) for i in getattr(ax, ''.join(['get_', w, 'ticklabels']))()],
                          'fontfamily': lambda ax, w, v: [i.set_family(v) for i in getattr(ax, ''.join(['get_', w, 'ticklabels']))()]},
           'label': {'color': lambda ax, w, v: getattr(ax, ''.join(['get_', w, 'axis']))().get_label().set_color(v),
                     'fontsize': lambda ax, w, v: getattr(ax, ''.join(['get_', w, 'axis']))().get_label().set_size(v),
                     'fontfamily': lambda ax, w, v: getattr(ax, ''.join(['get_', w, 'axis']))().get_label().set_family(v)},
           'ticks': {'color': lambda ax, w, v: ax.tick_params(axis=w, color=v),
                     'below': lambda ax, w, v: ax.set_axisbelow(v),
                     'direction': lambda ax, w, v: [i._apply_params(tickdir=v) for i in getattr(ax, ''.join(['get_', w, 'axis']))().get_major_ticks() + getattr(ax, ''.join(['get_', w, 'axis']))().get_major_ticks()]},
           'grid': {'color': lambda ax, w, v: ax.grid(color=v),
                    'linewidth': lambda ax, w, v: ax.grid(linewidth=v),
                    'dashes': lambda ax, w, v: ax.grid(dashes=v),
                    'linestyle': lambda ax, w, v: ax.grid(linestyle=v),
                    'visible': lambda ax, w, v: ax.grid(visible=v),
                    'style': Alias('grid', 'linestyle')},
           'face': {'color': lambda ax, w, v: ax.set_facecolor(v)},
           'legend': {'fontfamily': lambda ax, w, v: [i.set_family(v) for i in ax.get_legend().get_texts()],
                      'fontsize': lambda ax, w, v: [i.set_fontsize(v) for i in ax.get_legend().get_texts()],
                      'color': lambda ax, w, v: [i.set_color(v) for i in ax.get_legend().get_texts()]}
           }

class StyleError(Exception):
    pass

styles = {
    'ggplot_like': {
        'face:color': '#E5E5E5', 'grid:color': 'white', 'grid:linestyle': (0.5, (1, 4)), 'grid:linewidth': 1.3,
        'label:color': '#555555', 'spine:color': '#D5D5D5', 'ticklabels:color': '#555555', 'ticks:color': '#555555',
        'ticks:direction': 'out', 'grid:visible': True
    },
    'inverse_ggplot': {
        'face:color': '#F1F1F1', 'grid:color': '#C3C3C3', 'grid:linestyle': (0.5, (1, 4)), 'grid:linewidth': 0.8,
        'label:color': 'black', 'spine:color': '#D5D5D5', 'ticklabels:color': 'black', 'ticks:color': '#555555',
        'ticks:direction': 'out', 'grid:visible': True
    },
    'inverse_ggplot_straight': {
        'face:color': '#F1F1F1', 'grid:color': '#C3C3C3', 'grid:linestyle': 'solid', 'grid:linewidth': 0.8,
        'label:color': 'black', 'spine:color': '#D5D5D5', 'ticklabels:color': 'black', 'ticks:color': '#555555',
        'ticks:direction': 'out', 'grid:visible': True
    },
    'inverse_ggplot_straight_solid_border': {
        'face:color': '#F1F1F1', 'grid:color': '#C3C3C3', 'grid:linestyle': 'solid', 'grid:linewidth': 0.8,
        'label:color': 'black', 'spine:color': 'black', 'ticklabels:color': 'black', 'ticks:color': '#555555',
        'ticks:direction': 'out', 'grid:visible': True
    },
    'vega-lite': {
        'face:color': 'white', 'grid:visible': True, 'grid:color': '#DFDFDF', 'grid:style': 'solid', 'label:color': 'black',
        'spine:top:color': 'white', 'spine:right:color': 'white', 'spine:bottom:color': 'black',
        'spine:left:color': 'black', 'ticklabels:color': 'black', 'ticks:color': 'black', 'ticks:direction': 'out'
    },
    'adefault': {
        'face:color': 'white', 'grid:visible': False, 'label:color': 'black', 'spine:color': 'black',
        'ticklabels:color': 'black', 'ticks:color': 'black', 'ticks:direction': 'out'
    }
}

class Style(dict):
    """
    Style for Matplotlib axes
    It is essentially a dictionary with overriden methods
    Usage: (assume ax is an matplotlib axes object
        .. code:: python
            style = Style()
            style.apply_to_ax(ax)
            style.update({selector: value})  # or use style.update_style
            style['selector']=value  # this also updates the axes object
            # if you have done some modifications to the plot yourself and want to update the style again use
            style.reapply()

    Note: instead of working with the Style object directly you can use ax.current_style after you applied a style
    Note: You can apply one Style object to more than one axes object. Just call apply_to_ax multiple times or with a list of axes
        If you applied one Style to multiple axes objects and you use axes.current_style instead of the style object
        directly the updates/changes will nonetheless be applied to all applied axes objects
    """
    def __init__(self, iterable={}, **kwargs):
        super(Style, self).__init__(iterable, **kwargs)
        self.ax = []
        self.fig = []

    def apply_to_ax(self, ax):
        """
        Apply this style to the given axes object
        You can apply to multiple axes objects by calling this multiple times or with a list of objects
        :param ax: matplotlib axes object or list of those
        """
        ax = ax if isinstance(ax, list) else [ax,]
        for a in ax:
            a.current_style = self
        self.ax.extend(ax)
        self.reapply()

    def apply_to_fig(self, fig):
        """
        Apply this style to the given figure and its axes (and new axes)
        You can apply to multiple figures by calling this multiple times or with a list of figures
        :param fig: matplotlib figure or list of those
        :return:
        """
        fig = fig if isinstance(fig, list) else [fig,]
        for f in fig:
            self.apply_to_ax(f.axes)
            f.current_style = self
        self.fig.extend(fig)
        self.reapply()

    def _get_list_of_ax(self):
        l = []
        for f in self.fig:
            l.extend(f.axes)
        l.extend(self.ax)
        return l

    def update(self, E=None, **F):
        """
        Update the value in the internal dictionary and update the axes object
        :param E: dictionary with key/value pairs to update
        """
        if(hasattr(self, 'ax')):
            for a in self._get_list_of_ax():
                dict = _style_plot(E, axes=a)
        else:
            warn("No axes object was associated to this style. Use apply_to_ax first")
        super(Style, self).update(dict)

    def update_style(self, E):
        """
        more explicit alias to ``update``
        """
        self.update(E)

    def reapply(self):
        """
        reapply this style to the axes object
        :return:
        """
        if(hasattr(self, 'ax')):
            for a in self._get_list_of_ax():
                _style_plot(self, axes=a)
        else:
            warn("No axes object was associated to this style. Use apply_to_ax first")

    def __setitem__(self, key, value):  # this may be not beautiful but it does auto update on the plot
        """
        Set a value and update the axes object
        """
        self.update({key: value})


def _apply_style(sel, sub, attr, value, axes):  # if the method does not require a subsel then subsel is to be []
    if not isinstance(sub, list):
        sub = [sub,]
    if len(sub) == 0:
        methods[sel][attr](axes, sub, value)
    else:
        for s in sub:
            methods[sel][attr](axes, s, value)


def _split_key(key):
    try:
        if key.count(":") == 2:
            sel, subsel, attr = key.split(":")
        else:
            sel, attr = key.split(":")
            subsel = ''
    except ValueError:
        raise StyleError("Not enough specifiers")
    if sel not in selectors:
        raise StyleError("Unknown specifier: "+sel)
    else:
        if subsel == '':
            subsel = selectors[sel][0]
    if isinstance(subsel, str) and len(selectors[sel][0]) > 0 and subsel not in selectors[sel][0]:
        raise StyleError("Unknown sub specifier: "+subsel)
    elif attr not in selectors[sel][1]:
        raise StyleError("Unknown attribute: "+attr)

    return sel, subsel, attr


def _style_plot(config=None, axes=None):
    """
    Style a plot
    format of config_dict:
        {'top_selector:sub_selector:attribute': value}
        you can omit sub_selector if you want to set a value for the attribute of all sub_selectors.
        Format for that looks like so: 'top_selector::attribute' note the double colon
    :param config: dictionary with style options or string with stylename (see styles variable in this module)
    :param axes: (optional) the axes object to style. Default is to use the current object (plt.gca())
    :return:
    """
    if isinstance(config, str):
        if config in styles:
            return _style_plot(styles[config], axes)
        else:
            raise StyleError("Style does not exist: "+config)
    for key, value in config.items():
        sel, subsel, attr = _split_key(key)

        if axes is None:
            axes = plt.gca()

        _apply_style(sel, subsel, attr, value, axes)
    return config