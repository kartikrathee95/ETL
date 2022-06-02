import sys
import abc
import time
import traceback
import signal
#import gevent
from kafka_logger import logger


__all__ = [
    'QueueDefBuilder',
    'QueueProcessor'
]

class GracefulKiller:
    """Do not let program to exit in middle of your processing logic.
    Override system kill signal handlers and give you a cleanup window.

    Usage:
    >>> killer = GracefulKiller()
    ... while not killer.kill_now:
    ...     data = pop_from_queue()
    ...     # your logic here
    ...     # NOTE: <5 seconds logic


    NOTE: If your loop is taking more than 5 seconds to
    execute than you have to use raise_exception

    NOTE: Why this 5 second logic?

    If supervisor process doesn't stop in 10 second than supervisord
    send a KILL Signal. For safe side we are using 5 second as threshold.
    So we must have to exit in 5 seconds otherwise our program will be
    killed without a cleanup window.

    Usage if loop takes >5 seconds:
    >>> killer = GracefulKiller(raise_exception)
    ... while not killer.kill_now:
    ...     killer.end_processing()
    ...     data = None
    ...     try:
    ...         data = pop_from_queue()
    ...         killer.start_processing()
    ...
    ...         # your logic here
    ...     except SystemExit as e
    ...         # Graceful exit
    ...         if data is not None:
    ...             add_to_queue(data)
    ...     except Exception as e:
    ...         if killer.kill_now:
    ...             # gracefully killed
    ...             if data is not None:
    ...                 add_to_queue(data)
    ...             raise
    ...         # Not gracefull exit
    ...         # Exception is raised in code execution
    """

    def __init__(self, raise_exception=False):
        """
        raise_exception - If your processing logic is taking more than 5 seconds.
                            Than set it True & add except SystemExit block
                            as shown in usage example.
        """
        self.raise_exception = raise_exception

        self.processing_logic_started = False
        self.processing_logic_finished = False

        self.kill_now = False

        # gevent.signal(signal.SIGINT, self.exit_gracefully)
        # gevent.signal(signal.SIGTERM, self.exit_gracefully)

    def start_processing(self):
        if self.kill_now and self.raise_exception:
            # processing started after kill signal is received
            # we will not be able to process this data
            self.exit_program()

        self.processing_logic_started, self.processing_logic_finished = True, False

    def end_processing(self):
        self.processing_logic_started, self.processing_logic_finished = False, True

    # def exit_gracefully(self, signum, frame):
    def exit_gracefully(self):
        print('Kill Signal Received')

        self.kill_now = True

        if self.raise_exception:
            if self.processing_logic_started and not self.processing_logic_finished:
                # code is inside processing logic
                self.exit_program()

    def exit_program(self):
        print('Exiting Gracefully')
        sys.exit(signal.SIGINT)


class QueueDefBuilder:
    """Build queue_def for passing into QueueProcessor

    NOTE: Never build the queue_def dictionary yourself.
            Use these helper functions
    """
    @staticmethod
    def build_redis_queue_def(
        redis_connection,
        queues,
        error_queue=None,
        reprocess_queue=None,

        is_all_set_queues=False,
        is_set_queues=False,
        is_set_error_queue=False,
        is_set_reprocess_queue=False
    ):
        """RedisQueueManager definition for queues

        queues - list of queues names in order of priority

        is_all_set_queues - True if all queues(queues, error, reprocess) are set type

        is_set_queues - True if queues are set type

        is_set_error_queue - True if error queue is set type

        is_set_reprocess_queue - True if reprocess queue is set type
        """
        return {
            'queue_manager_type': 'redis',
            'redis': redis_connection,
            'queues': queues,
            'error_queue': error_queue,
            'reprocess_queue': reprocess_queue,
            'is_all_set_queues': is_all_set_queues,
            'is_set_queues': is_set_queues,
            'is_set_error_queue': is_set_error_queue,
            'is_set_reprocess_queue': is_set_reprocess_queue
        }

    @staticmethod
    def build_list_queue_def(data_list):
        """ListQueueManager definition for data list

        data_list - List of data to process. ['aapl', 'fb', 'tsla'] etc.
        """
        return {
            'queue_manager_type': 'list',
            'data': data_list,
        }


class InvalidQueueManagerType(Exception):
    pass


class InvalidQueueDef(Exception):
    pass


class QueueManager:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def has_data(self):
        """Return True if queue has more data to process"""
        return

    @abc.abstractmethod
    def pop(self):
        """Return (queue_name, data)"""
        return (None, None)

    @abc.abstractmethod
    def lpush(self, queue_name, data):
        """Push data to left of queue_name for reprocessing"""
        return

    @abc.abstractmethod
    def add_to_error_queue(self, data):
        """Add data to error queue"""
        return

    @abc.abstractmethod
    def get_error_queue_data(self):
        """Return data in error queue"""
        return

    @abc.abstractmethod
    def add_to_reprocess_queue(self, data):
        """Add data to reprocess queue"""
        return

    @abc.abstractmethod
    def get_reprocess_queue_data(self):
        """Return data in reprocess queue"""
        return


class ListQueueManager(QueueManager):

    def __init__(self, queue_def):
        self.data_list = queue_def['data']
        self.next_data_index = 0

        self.error_data_list = []
        self.reprocess_data_list = []

    def has_data(self):
        return self.next_data_index < len(self.data_list)

    def pop(self):
        data = self.data_list[self.next_data_index]
        self.next_data_index += 1
        return ('default', data)

    def lpush(self, queue_name, data):
        pass

    def add_to_error_queue(self, data):
        self.error_data_list.append(data)

    def get_error_queue_data(self):
        return self.error_data_list

    def add_to_reprocess_queue(self, data):
        self.reprocess_data_list.append(data)

    def get_reprocess_queue_data(self):
        return self.reprocess_data_list


class RedisQueueManager(QueueManager):
    """"Manage multiple queues

    NOTE: Use build_redis_queue_def functions to build queue_def

    queue_def
    1) redis - redis connection object
    2) queues - list of queues names
    3) error_queue
    """

    def __init__(self, queue_def):
        self.queue_def = queue_def
        self.redis_connection = queue_def['redis']
        self.queues = queue_def['queues']
        self.error_queue = queue_def.get('error_queue')
        self.reprocess_queue = queue_def.get('reprocess_queue')

        self.is_all_set_queues = queue_def.get('is_all_set_queues', False)

        self.is_set_queues = queue_def.get('is_set_queues', False)
        self.is_set_error_queue = queue_def.get('is_set_error_queue', False)
        self.is_set_reprocess_queue = queue_def.get(
            'is_set_reprocess_queue', False
        )

        self._validate_queue_def()

    @property
    def queue_type_single(self):
        return len(self.queues) == 1

    @property
    def queue_type_multiple(self):
        return len(self.queues) > 1

    def _validate_queue_def(self):
        if not self.redis_connection:
            raise InvalidQueueDef('Redis not given')
        if not self.queues:
            raise InvalidQueueDef('No queues names given')
        if self.error_queue == '':
            raise InvalidQueueDef('Empty error_queue name')

    def has_data(self):
        # redis queue always has data
        return True

    def pop(self):
        """Return (queue_name, data) or (None, None)"""
        for queue_name in self.queues:
            if self.is_all_set_queues or self.is_set_queues:
                data = self.redis_connection.spop(queue_name)
            else:
                data = self.redis_connection.lpop(queue_name)
            if data is not None:
                return (queue_name, data)
        return (None, None)

    def lpush(self, queue_name, data):
        if queue_name not in self.queues:
            raise ValueError('Invalid queue_name: {}'.format(queue_name))

        if self.is_all_set_queues or self.is_set_queues:
            self.redis_connection.sadd(queue_name, data)
        else:
            self.redis_connection.lpush(queue_name, data)

    def _is_push_to_error_queue(self):
        if self.queue_type_multiple:
            return True

        queue_name = self.queues[0]
        if queue_name != self.error_queue:
            return True

        if self._get_error_queue_size() > 5:
            return True

        # error queue is same as main queue
        # & size of error queue is less than 5
        # So don't push the ticker
        # Why?
        # error will keep coming on slack
        return False

    def _get_error_queue_size(self):
        if not self.error_queue:
            return 0
        elif self.is_all_set_queues or self.is_set_error_queue:
            return self.redis_connection.scard(self.error_queue)
        else:
            return self.redis_connection.llen(self.error_queue)

    def add_to_error_queue(self, data):
        if self.error_queue:
            while True:
                try:
                    if not self._is_push_to_error_queue():
                        return

                    if self.is_all_set_queues or self.is_set_error_queue:
                        self.redis_connection.sadd(self.error_queue, data)
                    else:
                        self.redis_connection.rpush(self.error_queue, data)
                    return
                except Exception:
                    # Redis is down. Not able to add data in error queue
                    # try after every 2 minutes
                    print(traceback.format_exc())
                    time.sleep(2*60)

    def get_error_queue_data(self):
        if not self.error_queue:
            return []
        if self.is_all_set_queues or self.is_set_error_queue:
            return self.redis_connection.smembers(self.error_queue)
        else:
            return self.redis_connection.lrange(self.error_queue, 0, -1)

    def add_to_reprocess_queue(self, data):
        if not self.reprocess_queue:
            return
        elif self.is_all_set_queues or self.is_set_reprocess_queue:
            self.redis_connection.sadd(self.reprocess_queue, data)
        else:
            self.redis_connection.rpush(self.reprocess_queue, data)

    def get_reprocess_queue_data(self):
        if not self.reprocess_queue:
            return []

        if self.is_all_set_queues or self.is_set_reprocess_queue:
            return self.redis_connection.smembers(self.reprocess_queue)
        else:
            return self.redis_connection.lrange(self.reprocess_queue, 0, -1)


def _create_queue_manager(queue_def):
    manager_type = queue_def.get('queue_manager_type', 'redis')
    if manager_type == 'redis':
        return RedisQueueManager(queue_def)
    elif manager_type == 'list':
        return ListQueueManager(queue_def)
    raise InvalidQueueManagerType(
        'Invalid queue_manager_type: {}'.format(manager_type)
    )


class QueueProcessor:
    """Process entities from queues

    This class do following functions:
    - pop data from queue
    - call process_callback function to process that data
    - Add data in error queue if error occurs during processing
    - call logger.capture_exception when exception happens
    - repush data in queue when program exited during processing

    queue_def - see above build_*_queue_def functions

    process_callback(queue_processor, queue_name, queue_data)
    - queue_name & queue_data will be None when queue is empty.
    - No need to add sleep in this function

    Usage:

    >>> def process_callback(queue_processor, queue_name, data):
    ...     if data is None:
    ...         return
    ...     do_your_work(data)
    ...
    >>> queue_def = build_redis_queue_def(redis, ['queue_name'])
    >>> processor = QueueProcessor(queue_def, process_callback)
    >>> processor.start_processing()
    """

    def __init__(
        self,
        queue_def,
        process_callback,
        error_callback=None,
        cleanup_callback=None,
        heartbeat=None,
        sleep_time_when_queue_empty=60,
        entity_type='account',
        continous_error_sleep_time=10*60,
        num_of_continous_errors_to_sleep=2
    ):
        self.queue_manager = _create_queue_manager(queue_def)

        self.process_callback = process_callback
        self.error_callback = error_callback
        self.cleanup_callback = cleanup_callback

        self.heartbeat = heartbeat
        self.sleep_time_when_queue_empty = sleep_time_when_queue_empty
        self.entity_type = entity_type
        self.continous_error_sleep_time = continous_error_sleep_time
        self.num_of_continous_errors_to_sleep = num_of_continous_errors_to_sleep

    def start_processing(self):

        def enqueue_data(queue_name, data):
            if queue_name and data:
                self.queue_manager.lpush(queue_name, data)
                logger.info(
                    'Repushed in queue:', queue_name, data,
                    entity_type=self.entity_type, entity_value=data
                )
                if self.cleanup_callback:
                    self.cleanup_callback(self, queue_name, data)

        def reprocess_callback(entity_type, entity_value, extra):
            if entity_type == self.entity_type:
                self.queue_manager.add_to_reprocess_queue(entity_value)

        logger.add_reprocess_callback(reprocess_callback)

        num_of_continous_crashes = 0
        killer = GracefulKiller(raise_exception=True)

        while not killer.kill_now and self.queue_manager.has_data():
            killer.end_processing()
            queue_name, data = None, None
            try:
                queue_name, data = self.queue_manager.pop()
                killer.start_processing()

                self.process_callback(self, queue_name, data)

                if self.heartbeat:
                    self.heartbeat.beat()

                if data is None and self.sleep_time_when_queue_empty > 0:
                    # queue is empty so sleeping
                    print('Sleeping for {} seconds'.format(
                        self.sleep_time_when_queue_empty
                    ))
                    time.sleep(self.sleep_time_when_queue_empty)

                num_of_continous_crashes = 0
            except SystemExit as e:
                # Program gracefully exiting
                print('Graceful SystemExit')
                enqueue_data(queue_name, data)
                print('Graceful SystemExit repushed')
            except Exception as exc:
                if killer.kill_now:
                    # Program gracefully exiting
                    print('Captured Graceful Exit exception')
                    enqueue_data(queue_name, data)
                    print('Ticker repushed to queue')
                    raise

                killer.end_processing()

                if queue_name and data:
                    self.queue_manager.add_to_error_queue(data)

                if self.error_callback:
                    self.error_callback(self, exc, queue_name, data)

                logger.capture_exception(
                    exc,
                    entity_type=self.entity_type,
                    entity_value=data,
                    extra={
                        'queue': queue_name
                    }
                )

                num_of_continous_crashes += 1
                if num_of_continous_crashes >= self.num_of_continous_errors_to_sleep:
                    msg = 'Multiple error occurs continously. So sleeping for {} seconds'.format(
                        self.continous_error_sleep_time
                    )
                    print(msg)
                    time.sleep(self.continous_error_sleep_time)








