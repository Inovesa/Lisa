from ..internals import config_options, _check_compiled_version
if config_options.get("use_cython"):
    try:
        from .data_cython import Data
        from ..data import data_cython as data
        _check_compiled_version(data)
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .data import Data

    try:
        from .file_cython import Axis, File, MultiFile, DataError, DataContainer, DataNotInFile
        from ..data import file_cython as file
        _check_compiled_version(file)
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .file import Axis, File, MultiFile, DataError, DataContainer, DataNotInFile
else:
    from .data import Data
    from .file import Axis, File, MultiFile, DataError, DataContainer, DataNotInFile
