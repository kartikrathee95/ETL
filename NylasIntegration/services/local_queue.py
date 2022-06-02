
from config import get_redis_config
import redis

# REDIS_CONNECTION = get_redis_config()

MAIN_REDIS_CONNECTIONS_POOL = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
REDIS_CONNECTION = redis.Redis(connection_pool=MAIN_REDIS_CONNECTIONS_POOL, socket_timeout=2,
                                socket_connect_timeout=2)


class Queue:

    def __init__(self, name):
        self.name = name
        self.redisConn = REDIS_CONNECTION

    def count(self):
        return self.redisConn.llen(self.name)

    def write(self, msg):
        # raw_msg = msg.get_body()
        self.redisConn.rpush(self.name, msg)

    def read(self):
        if not self.count():
            return None
        raw_msg = self.redisConn.lindex(self.name, 0)  # returning element at index 0
        # msg = RawMessage(self)
        # msg.set_body(raw_msg)
        return raw_msg

    def delete_message(self, raw_msg):
        if self.count():
            self.redisConn.lpop(self.name)


class LocalQueueSystem:


    def get_queue(queue_name):
        q = Queue(queue_name)
        return q

    def create_queue(queue_name):
        return Queue(queue_name)