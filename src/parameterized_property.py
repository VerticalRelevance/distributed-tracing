class ParameterizedProperty:
    """A descriptor class that allows getters and setters with arguments"""

    def __init__(self, fget=None, fset=None):
        self.fget = fget
        self.fset = fset
        self.__doc__ = fget.__doc__ if fget else None

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        # Return a callable that will accept arguments and pass them to fget
        def getter(*args, **kwargs):
            return self.fget(obj, *args, **kwargs)

        return getter

    def __set__(self, obj, value):
        # For direct assignment without arguments, call setter with just the value
        self.fset(obj, value)

        # Create a wrapper that allows calling with additional parameters
        def setter_wrapper(**kwargs):
            return self.fset(obj, value, **kwargs)

        # Store this for later access
        obj.__dict__[f"_{self.fget.__name__}_setter"] = setter_wrapper

    def setter(self, fset):
        # Create a new instance with the same getter but new setter
        return type(self)(self.fget, fset)
