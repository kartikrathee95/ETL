from kafka_logger import logger
from functools import wraps

def log_function(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        message = 'Function: {0}'.format(fn.func_name)

        class_name = args[0].__class__.__name__ if args and hasattr(args[0], '__class__') else ''
        if class_name:
            message += ', Class: {0}'.format(class_name)

        logger.debug('Entering {0}'.format(message))

        result = fn(*args, **kwargs)

        logger.debug('Exiting {0}'.format(message))
        return result
    return wrapper