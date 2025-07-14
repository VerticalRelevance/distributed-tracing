# pylint: disable=line-too-long
"""
Parameterized Property Module

This module provides a descriptor class that extends Python's property functionality
by allowing both getters and setters to accept additional arguments. This is useful
for creating more flexible property interfaces where the property access might need
to be parameterized.

Example:
    ```python
    class MyClass:
        def __init__(self):
            self._data = {}

        @ParameterizedProperty
        def item(self, key):
            return self._data.get(key)

        @item.setter
        def item(self, value, key=None):
            self._data[key] = value

    obj = MyClass()
    obj.item('x')  # Calls getter with 'x' as key
    obj.item = 10  # Sets default value
    obj.item_setter(key='y')(20)  # Sets value 20 with key 'y'
    ```

Classes:
    ParameterizedProperty: A descriptor class for parameterized property access.
"""
# pylint: enable=line-too-long


class ParameterizedProperty:
    # pylint: disable=line-too-long
    """
    A descriptor class that allows getters and setters with arguments.

    This descriptor extends the standard property descriptor by allowing both getters
    and setters to accept additional arguments. It provides a way to create properties
    that can be accessed with parameters, similar to indexers in other languages.

    Attributes:
        fget: The function to be used for getting the attribute value.
        fset: The function to be used for setting the attribute value.
    """
    # pylint: enable=line-too-long

    def __init__(self, fget=None, fset=None):
        # pylint: disable=line-too-long
        """
        Initialize the parameterized property.

        Args:
            fget: Optional function to be used for getting the attribute value.
            fset: Optional function to be used for setting the attribute value.
        """
        # pylint: enable=line-too-long

        self.fget = fget
        self.fset = fset
        self.__doc__ = fget.__doc__ if fget else None

    def __get__(self, obj, objtype=None):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Get the property value.

        When accessed on a class, returns the descriptor itself.
        When accessed on an instance, returns a callable that accepts arguments
        to pass to the getter function.

        Args:
            obj: The instance the attribute was accessed through, or None when
                the attribute is accessed through the class.
            objtype: The class that was used to access the attribute.

        Returns:
            Either the descriptor itself (if accessed on the class) or a callable
            getter function that accepts additional arguments.
        """
        # pylint: enable=line-too-long

        if obj is None:
            return self

        # Return a callable that will accept arguments and pass them to fget
        def getter(*args, **kwargs):
            return self.fget(obj, *args, **kwargs)

        return getter

    def __set__(self, obj, value):
        # pylint: disable=line-too-long
        """
        Set the property value.

        Handles direct assignment to the property and also creates a wrapper function
        that allows setting the property with additional parameters.

        Args:
            obj: The instance on which to set the attribute.
            value: The value to set.
        """
        # pylint: enable=line-too-long

        # For direct assignment without arguments, call setter with just the value
        self.fset(obj, value)

        # Create a wrapper that allows calling with additional parameters
        def setter_wrapper(**kwargs):
            return self.fset(obj, value, **kwargs)

        # Store this for later access
        obj.__dict__[f"_{self.fget.__name__}_setter"] = setter_wrapper

    def setter(self, fset):
        # pylint: disable=line-too-long
        """
        Decorator to set the setter function.

        Similar to the property.setter decorator, this allows defining the setter
        function after the getter has been defined.

        Args:
            fset: The function to use as the setter.

        Returns:
            A new ParameterizedProperty instance with the same getter but the new setter.
        """
        # pylint: enable=line-too-long

        # Create a new instance with the same getter but new setter
        return type(self)(self.fget, fset)
