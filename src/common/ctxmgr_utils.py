"""
High-Precision Timing Context Manager Utilities

This module provides a singleton utility class for measuring execution time of code blocks
with high precision using Python's platform-independent timing mechanisms.

The module implements a context manager-based approach to timing that offers:
- Precise time measurement using timeit.default_timer
- Singleton pattern for consistent timing across the application
- Platform-independent timing functionality
- Real-time elapsed time access during execution
- Final elapsed time retrieval after execution

Classes:
    CtxMgrUtils: Singleton utility class providing elapsed time context managers

Key Features:
    - Singleton Design Pattern: Ensures consistent timing instance across application
    - High-Precision Timing: Uses timeit.default_timer for maximum accuracy
    - Context Manager Support: Clean, readable timing with automatic cleanup
    - Platform Independence: Works consistently across different operating systems
    - Real-time Access: Query elapsed time during execution, not just at completion

Usage Examples:
    Basic timing measurement:
        >>> utils = CtxMgrUtils()
        >>> with utils.elapsed_timer() as timer:
        ...     # Perform time-critical operations
        ...     process_data()
        ...     intermediate_time = timer()  # Check progress
        ...     process_more_data()
        >>> total_time = timer()  # Get final elapsed time
        >>> print(f"Total execution: {total_time:.3f} seconds")

    Performance monitoring:
        >>> utils = CtxMgrUtils()
        >>> with utils.elapsed_timer() as timer:
        ...     for i in range(1000):
        ...         expensive_operation(i)
        ...         if i % 100 == 0:
        ...             print(f"Progress: {i/10}%, Time: {timer():.2f}s")

    Nested timing contexts:
        >>> utils = CtxMgrUtils()
        >>> with utils.elapsed_timer() as outer_timer:
        ...     setup_operation()
        ...     with utils.elapsed_timer() as inner_timer:
        ...         core_operation()
        ...     print(f"Core: {inner_timer():.2f}s, Total: {outer_timer():.2f}s")

Dependencies:
    - contextlib: Provides @contextmanager decorator
    - timeit: Supplies default_timer for high-precision timing

Notes:
    - Timer precision is platform-dependent but optimized for each system
    - All times are returned as floating-point seconds
    - The context manager is reentrant and supports nesting
    - Singleton pattern ensures consistent behavior across modules
    - The yielded timer function can be called multiple times safely
"""
from contextlib import contextmanager
from timeit import default_timer

class CtxMgrUtils:
    # pylint: disable=line-too-long
    """
    A singleton utility class providing context managers for time measurement and
    performance monitoring.

    This class implements the singleton pattern and offers context managers for measuring
    execution time of code blocks. It provides precise timing functionality using Python's
    timeit.default_timer for maximum accuracy across different platforms.

    Features:
        - Singleton pattern implementation
        - High-precision time measurement
        - Context manager support
        - Platform-independent timing
        - Callable timer function access

    Methods:
        __new__(cls, *args, **kwargs): Creates singleton instance
        elapsed_timer(): Context manager for time measurement

    Time Measurement:
        - Uses timeit.default_timer for highest available precision
        - Platform-independent timing functionality
        - Provides both running and final elapsed time
        - Returns callable function for accessing elapsed time

    Context Manager Usage:
        The elapsed_timer context manager:
        - Starts timing when entering the context
        - Provides access to elapsed time during execution
        - Updates to final time when exiting context
        - Returns time in seconds with floating-point precision

    Example:
        >>> utils = CtxMgrUtils()  # Creates or returns existing instance
        >>> with utils.elapsed_timer() as timer:
        ...     # Perform operations
        ...     time.sleep(1)
        ...     current_time = timer()  # Get current elapsed time
        >>> final_time = timer()  # Get total elapsed time
        >>> print(f"Operation took {final_time:.2f} seconds")

    Timer Function:
        The yielded timer function:
        - Takes no arguments
        - Returns elapsed time in seconds
        - Can be called multiple times
        - Updates automatically at context exit

    Dependencies:
        - contextlib: For context manager implementation
        - timeit.default_timer: For high-precision timing
        - typing: For type hints

    Notes:
        - Timer precision depends on platform-specific implementation
        - All times are returned in seconds as floating-point numbers
        - The context manager is reentrant and can be nested
        - The singleton pattern ensures consistent timing across the application
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            CtxMgrUtils: The singleton instance of the class.
        """
        # pylint: enable=line-too-long

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @contextmanager
    def elapsed_timer(self):
        # pylint: disable=line-too-long
        """
        A context manager that measures the elapsed time of a code block.

        Provides a function to retrieve the elapsed time when exiting the block.
        The timer starts when entering the context and stops when exiting.

        Yields:
            function: A callable that returns the elapsed time in seconds.

        Example:
            with utils.elapsed_timer() as timer:
                # Code to measure
                time.sleep(1)
            print(f"Operation took {timer():.2f} seconds")
        """
        # pylint: enable=line-too-long

        start = default_timer()

        def elapsed_keeper():
            # pylint: disable=line-too-long
            """
            Returns the current elapsed time since the context manager was entered.

            This function is yielded by the context manager and can be called
            multiple times to get the current elapsed time. During the context
            block execution, it returns the time elapsed since entering the context.
            After exiting the context, it returns the total elapsed time.

            Returns:
                float: The elapsed time in seconds since the context manager was entered.
            """
            # pylint: enable=line-too-long

            return default_timer() - start

        yield elapsed_keeper
        end = default_timer()

        # pylint: disable=function-redefined
        def elapsed_keeper():
            # pylint: disable=line-too-long
            """
            Returns the final elapsed time after the context manager has exited.

            This redefined function replaces the original elapsed_keeper after
            the context block has finished executing. It provides the total
            elapsed time for the entire context block duration.

            Returns:
                float: The total elapsed time in seconds for the context block.
            """
            # pylint: enable=line-too-long

            return end - start
        # pylint: enable=function-redefined
