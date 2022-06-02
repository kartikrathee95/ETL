
import signal
import sys
import json
import logging
from datetime import datetime
import traceback
import time
# import boto3
# from boto.sqs.message import RawMessage
from kafka_logger import logger
from NylasIntegration.scripts.log_func import log_function
# from NylasIntegration.scripts.constants import QUEUE_USER_CALENDARS_ERROR, QUEUE_USER_CALENDARS
from NylasIntegration.services.sqs import Boto3SQSConn
from NylasIntegration.services.local_queue import LocalQueueSystem
import os
from config import settings

# if LOCAL:
# q__conn = LocalQueueSystem
if settings.DOMAIN in ['DEVELOPMENT']:
    q__conn = LocalQueueSystem
else:
    q__conn = Boto3SQSConn()


class ScriptHandler(object):
    kill_now = False
    _msg = None
    json_decode = True
    thread_local_data = True
    script_name = 'ScriptHandler'

    def __init__(self, queue_name, **options):
        self.queue_name = queue_name
        
        self.queue = q__conn.get_queue(self.queue_name)
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.sleep_time = 1
        self.script_name = self.inherited_class()
        # logging.basicConfig()
        # self.logger = logging.getLogger(self.script_name)

        self.debug = False
        self.message_visibility_timeout = None
        # self.logger = logging.getLogger()
        self.logger = logger
        start_info = 'Starting Script: {0}.'.format(self.script_name)
        queue_info = 'Name: {0}, Count: {1}.'.format(self.queue_name, self.queue.count())
        self.logger.info(start_info)
        self.logger.info(queue_info)
        # self.slack('{0} {1}'.format(start_info, queue_info), msg_type='info')
        self.start_time = None

        if options:
            self.logger.info('Options: ' + str(options))
        if 'sleep_time' in options:
            self.sleep_time = options['sleep_time']
        if 'json_decode' in options:
            self.json_decode = options['json_decode']
        if 'redis_processing_queue' in options:
            self.redis_processing_queue = options['redis_processing_queue']
        if 'debug' in options and options['debug']:
            self.debug = True
        if 'message_visibility_timeout' in options:
            self.message_visibility_timeout = options['message_visibility_timeout']
        if 'thread_local_data' in options:
            self.thread_local_data = options['thread_local_data']

    def read_from_queue(self):
        try:
            if self.message_visibility_timeout:
                self._msg = self.queue.read(self.message_visibility_timeout)
            else:
                self._msg = self.queue.read()
            self.start_time = time.time()
        except Exception as e:
            error = "Exception: " + str(e) + " Traceback: " + str(traceback.format_exc())
            self.logger.error(error)
            self.slack(error)
            time.sleep(self.sleep_time)
        return self.parse()

    # def set_thread_local(self, message):
    #     if isinstance(message, dict):  # if thread_data
    #         data = message.get('thread_data', '{}')
    #         data = json.loads(data)
    #         if data:
    #             copy_thread_local_dict(data, scriptname=self.script_name)
    #             return
    #     create_thread_local_dict(getattr(self, "callback", ''), AnonymousUser(), 'script', self.script_name)

    def inherited_class(self):
        class_name = self.__class__.__name__ if self and hasattr(self, '__class__') else 'ScriptHandler'
        return class_name

    def parse(self):
        if not self._msg:
            return None
        msg = self._msg.get_body()
        if not msg:
            return None
        if self.json_decode:
            msg = json.loads(msg)
        return msg

    # @log_function
    def remove_from_queue(self):
        if self._msg:
            self._msg.delete()
            print(datetime.now(), 'msg deleted ', self._msg.get_body())
            if self.start_time:
                exec_time = time.time() - self.start_time
                logger.info("EXECUTION_END. QueueName: {0} TimeTaken: {1}".format(self.queue_name, exec_time))
        else:
            warning = 'Empty message cannot be removed from Queue: ' + self.queue_name
            self.logger.warn(warning)

    @log_function
    def exit_gracefully(self, signum, frame):
        self.kill_now = True

    def printlog(self, *args):
        if self.debug:
            print(args)

    def execute(self):
        callback = getattr(self, "callback", None)
        if not callback:
            critical = 'Callback is not defined for Script: {0}. Exiting'.format(self.script_name)
            self.logger.critical(critical)
            self.slack('Callback is not defined for Script', msg_type='critical')
            return
        if not callable(callback):
            critical = 'Callback is not callable for Script: {0}. Exiting'.format(self.script_name)
            self.logger.critical(critical)
            self.slack('Callback is not callable for Script', msg_type='critical')
            return

        while True:
            self.process()

    def process(self):
        if self.kill_now:
            warning = 'Exiting Script: {0}. Count: {1}'.format(self.script_name, self.queue.count())
            self.logger.warn(warning)
            self.slack('Exiting Script. Count: {0}'.format(self.queue.count()), msg_type='warning')
            sys.exit(0)

        message = self.read_from_queue()
        if not message:
            return

        try:
            # if self.thread_local_data:
            #     self.set_thread_local(message)
            # This log is being added for ElastAlert.
            
            logger.info("QueueName: {0} QueueCount: {1}".format(self.queue_name, self.queue.count()))
            self.callback(message)
        # except custom_exceptions.NoteNotFoundError:
        #     logger.warn('Removing from queue since note we received note not found exception')
        #     self.remove_from_queue()
        except Exception as e:
            error = "Exception: {0} Traceback: {1}".format(str(e), str(traceback.format_exc()))
            # This log is being added for ElastAlert.
            self.logger.info("ScriptException exception in script: {}".format(self.script_name))
            self.logger.error(error)
            self.slack(error)

        del message

    # @log_function
    # def slack(self, msg, msg_type='error', other_channels=None):
    #     """

    #     :param msg: Message
    #     :param msg_type: DEFAULT: 'ERROR'.
    #     :param other_channels: DEFAULT: None(SLACK_NOTEBOOK_SQS_ERROR). single or list. Add list of recipients if want to receive on different channels
    #     """
    #     channels = [QUEUE_USER_CALENDARS_ERROR]
    #     if other_channels:
    #         if isinstance(other_channels, list):
    #             channels = other_channels
    #         else:
    #             channels = [other_channels]
        # send_to_slack(channels, '{0} - {1}, {2}, {3}: _{4}_\n'.format(USER_SERVER_DOMAIN, BASE_URL, self.script_name, msg_type.capitalize(), msg.lower()), 'root')

    # @log_function
    # def add_to_processing_queue(self, itemid):
    #     try:
    #         if self.redis_processing_queue:
    #             key = self.redis_processing_queue
    #             if REDIS_CONNECTION.type(key) == 'string':
    #                 REDIS_CONNECTION.delete(key)

    #             if not REDIS_CONNECTION.sismember(key, itemid):
    #                 REDIS_CONNECTION.sadd(key, itemid)
    #                 return 1
    #             else:
    #                 error = 'Cannot process this id {0}, it is a duplicate entry in {1}'.format(itemid, self.queue_name)
    #                 self.slack(error, other_channels=QUEUE_USER_CALENDARS_ERROR)
    #                 return 0
    #         else:
    #             error = 'No redis queue to add item to. Itemid {0}, Queue name: {1}'.format(itemid, self.queue_name)
    #             self.slack(error, other_channels=QUEUE_USER_CALENDARS_ERROR)
    #             return 0
    #     except TimeoutError as e:
    #         error = "Exception: {0} Traceback: {1}".format(str(e), str(traceback.format_exc()))
    #         self.logger.error(error)

    # @log_function
    # def remove_from_processing_queue(self, itemid):
    #     try:
    #         key = self.redis_processing_queue
    #         #res = REDIS_CONNECTION.get(self.redis_processing_queue)
    #         if not REDIS_CONNECTION.sismember(key, itemid):
    #             self.logger.error('ERROR: {0} {1}'.format(itemid, self.script_name))
    #             error = '{0} is already removed from this queue {1}'.format(itemid, self.queue_name)
    #             self.slack(error, other_channels=QUEUE_USER_CALENDARS_ERROR)
    #             return 0
    #         else:
    #             REDIS_CONNECTION.srem(key, itemid)
    #             return 1
    #     except TimeoutError as e:
    #         error = "Exception: {0} Traceback: {1}".format(str(e), str(traceback.format_exc()))
    #         self.logger.error(error)

    @log_function
    def update_visibility(self, visibility_timeout):
        if self._msg:
            self._msg.change_visibility(visibility_timeout)

    # @log_function
    def add_message_to_queue(self, message_json):
        # if type(message_json) is not dict:
        #     return

        # new_message = RawMessage()
        # new_message.set_body(json.dumps(message_json))    
        self.queue.write(message_json)
        print(message_json)
        logger.info("Added to Queue. QueueName: {0} Calendar: {1}".format(self.queue_name, message_json))
        return

"""Script Handler can be used for:
   1.) It will handle Sigterm(Ctrl + C) and SigInt (Sys kill) signals for graceful exit giving
       enough time for script to finish current task.
   2.) It will set self.logger whose configuration will be set as in supervisor conf (Rotating Logger).
   3.) It will handle the basic queue operation. 1.) read , 2.) delete. Child script cannot directly access queue.
   4.) It will run the child script main function (must be named as callback) in forever while loop giving the child.
       script message which will be checked for errors and also json decoded before passing it on.
   5.) It will alert script info: Start time , End time, Queue Count etc.

   Things to do before inheriting ScriptHandler:
   1.) Call parent constructor in your constructor passing queue name as only param.
   2.) Write callback function in your script.
   3.) Callback function should have only one argument [message].
   4.) Use self.logger for logging.
   5.) Call the parent execute function.
"""

# Things to

