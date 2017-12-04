from ..internals import config_options, _check_compiled_version
if config_options.get("use_cython"):
    try:
        from .data_cython import Data
        from ..data import data_cython as dats
        _check_compiled_version(dats)
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .data import Data

    try:
        from .file_cython import Axis, File, MultiFile, DataError, DataContainer
        from ..data import file_cython as files
        _check_compiled_version(files)
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .file import Axis, File, MultiFile, DataError, DataContainer
else:
    from .file import Axis, File, MultiFile, DataError, Datacontainer
