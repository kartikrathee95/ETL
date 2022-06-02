import boto3

try:
    BOTO3_SQS_CLIENT = boto3.client('sqs', region_name='us-east-1')
except:
    BOTO3_SQS_CLIENT = None


# Boto3 sqs msg class to imitate the boto2 methods for 1 message
class Boto3SQSConn:

    def create_queue(queue_name):
        q = BOTO3_SQS_CLIENT.create_queue(QueueName=queue_name,
                                            Attributes={"DelaySeconds": "0"})
    def get_queue(self, queue_name):
        q = Boto3SQSQueue(queue_name)
        return q


class Boto3SQSQueue:

    client = None
    queue_name = None
    receipt_handle=None
    wait_time = 1
    max_messages = 1
    QUEUE_URL_PREFIX = 'https://queue.amazonaws.com/602037364990/'

    def __init__(self, queue_name, wait_time=20):
        self.queue_name = queue_name
        self.queue_url = self.QUEUE_URL_PREFIX + queue_name
        self.client = BOTO3_SQS_CLIENT
        self.wait_time = wait_time
        self.receipt_handle = None
        self.msg_body = '{}'
        self.receive_status = None
        self.msg = None

    def readUtil(self):
        if not self.client:
            raise Exception('SQS Client not found')
        response = self.client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=self.max_messages,
            WaitTimeSeconds=self.wait_time
        )
        if response:
            message = response.get('Messages', [{}])[0]
            self.receipt_handle = message.get('ReceiptHandle')
            msg = message.get('Body')
            self.receive_status = True
            self.msg = 'Success'
            if not msg:
                return None
            self.msg_body = msg
            return self
        else:
            raise Exception('Response is empty from sqs queue: %s' %(self.queue_name))

    def read(self):
        try:
            return self.readUtil()
        except Exception as exp:
            self.receive_status = False
            self.msg = str(exp)
            return None

    def delete(self):
        try:
            response = self.client.delete_message(
                        QueueUrl = self.queue_url,
                        ReceiptHandle = self.receipt_handle)
            status = response.get('ResponseMetadata',{}).get('HTTPStatusCode',False)
            status = True if status==200 else False
        except:
            status=False
        return status

    def count(self):
        c=0
        if self.client:
            try:
                response = self.client.receive_message(QueueUrl=self.queue_url, MaxNumberOfMessages=1, AttributeNames=['All'])
                message = response.get('Messages', [{}])[0]
                c = message.get('Attributes', {}).get('ApproximateReceiveCount', 0)
                c = int(c)
            except:
                c=0
        return c

    def get_body(self):
        return self.msg_body

    def write(self, msg):
        status=True
        try:
            # raw_msg = msg.get_body()
            self.client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=msg
            )
        except:
            status=False
        return status