# -*-coding: utf8 -*
from functools import wraps
from timeit import default_timer


def timer(function):
    """
    :param function: func
    :type function: func
    :return: func
    :rtype: func
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        """
        :param args: func
        :type args: func
        :return: func
        :rtype: func
        """
        start_time = default_timer()
        result = function(*args, **kwargs)
        elapsed = default_timer() - start_time
        print('"{name}" completed in {time}s.'.format(name=function.__name__, time=round(elapsed, 4)))
        return result
    return wrapper
