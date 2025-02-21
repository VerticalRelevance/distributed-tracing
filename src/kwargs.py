def show_args_kwargs(required_param, *args, **kwargs):
    # Print the required named parameter
    print(f"Required parameter:")
    print(f"  {required_param}")

    # Print all positional arguments
    print("\nPositional arguments (*args):")
    for arg in args:
        print(f"  {arg}")

    # Print all keyword arguments
    print("\nKeyword arguments (**kwargs):")
    for key, value in kwargs.items():
        print(f"  {key}: {value}")


# Create a dictionary of parameters
params = {"name": "Alice", "age": 30, "city": "Seattle"}

# Call the function with a named argument, regular arguments, and the dictionary as kwargs
# show_args_kwargs("I am required!", "Hello", 123, True, **params)
show_args_kwargs("I am required!", None, **params)
