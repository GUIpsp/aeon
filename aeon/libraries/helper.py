import importlib
import inspect
from functools import reduce


def aefunction(str, f2):
    def typee(f):
        f.__aetype__ = str
        f.__function__ = f2
        return f

    return typee


# Returns a dict with the function implementations {name: (specification, function), ...}
def importNative(path, function_name):
    result = {}
    bib = importlib.import_module(path)
    # Imports everything
    if function_name == '*':
        for name in dir(bib):
            result = {**result, **importNative(path, name)}
    else:
        function = getattr(bib, function_name)
        
        if hasattr(function, '__aetype__'):
            typee = getattr(function, '__aetype__')
            function = getattr(function, '__function__')
            result[function_name] = (typee, function)
    return result