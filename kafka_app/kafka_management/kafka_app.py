import asyncio
import atexit
from datetime import datetime
import json
import logging
import time
import uuid
import threading
from confluent_kafka import Producer, Consumer, KafkaError, Message
from typing import Optional
from kafka_app.kafka_management.kafka_topic import KafkaMessage, Topic
from kafka_app.kafka_management.kafka_router import KafkaRouter
from typing import List, Callable
from confluent_kafka.admin import AdminClient, NewTopic
import uuid

# sample usage: start_thread(lambda: func(*args, **kwargs))
def non_blocking(func):
    threading.Thread(target=func).start()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

logger = logging.getLogger(__name__)


class KafkaApp:
    def __init__(
        self,
        service_name: str,
        brokers: str,
        sasl_username: Optional[str] = None,
        sasl_password: Optional[str] = None,
        sasl_mechanism: str = "SCRAM-SHA-512",
        security_protocol: str = "SASL_SSL",
        _router_response_timeout: int = 30,
        _logger=logger,
        _commit_after_received_message_count=100,
    ):
        self.service_name = service_name

        basic_config = {
            "bootstrap.servers": brokers,
        }
        if sasl_username is not None or sasl_password is not None:
            basic_config = {
                "bootstrap.servers": brokers,
                "sasl.mechanisms": sasl_mechanism,
                "security.protocol": security_protocol,
                "sasl.username": sasl_username,
                "sasl.password": sasl_password,
            }
        # Admin
        self.admin_client = AdminClient(basic_config)

        # Consumer
        consumer_config = {
            "group.id": service_name,
            "auto.offset.reset": "earliest",
            # Do not advance committed offsets outside the transaction.
            # Consumer offsets are committed along with the transaction
            # using the producer's send_offsets_to_transaction() API.
            "enable.auto.commit": False,
            "enable.partition.eof": True,
            # When set to read_committed, the consumer will only be able to read records
            # from committed transactions (in addition to records not part of transactions)
            "isolation.level": "read_committed",
            "broker.version.fallback": "3.6.1",
            "broker.address.family": "v4",
            "heartbeat.interval.ms": "3000",
        }
        consumer_config.update(basic_config)
        self.consumer = Consumer(consumer_config)

        # Producer
        producer_config = {
            "transactional.id": str(uuid.uuid4()),
            "broker.version.fallback": "3.6.1",
            "broker.address.family": "v4",
        }
        producer_config.update(basic_config)
        self.producer = Producer(producer_config)

        # Init transactions
        self.producer.init_transactions()
        self.producer.begin_transaction()

        # Router
        self.router = KafkaRouter(response_timeout=_router_response_timeout)

        # Logger
        self._logger = _logger

        # commit queue
        self._commit_after_received_message_count = _commit_after_received_message_count
        
        self.commit_call = asyncio.Queue()
        threading.Thread(target=self._wait_for_commit).start()

    def delivery_report(self, err, msg):
        if err is not None:
            self._logger.info(
                "Message delivery failed ({} [{}]): {}".format(
                    msg.topic(), str(msg.partition()), err
                )
            )
            return
        self._logger.info(
            "Message {} successfully produced to {} [{}] at offset {}".format(
                msg.key(), msg.topic(), msg.partition(), msg.offset()
            )
        )

    def send(
        self,
        topic: Topic,
        request_id: Optional[str] = None,
        message_key: Optional[str] = None,
    ) -> Optional[KafkaMessage]:
        req_id = request_id or str(uuid.uuid4())

        topic.headers["request_id"] = req_id

        self._logger.info(
            "=== Producing message to {} === \n {} \n {}".format(
                topic.name, topic.headers, topic.data
            )
        )

        self.producer.produce(
            topic=topic.name,
            value=json.dumps(topic.data).encode(),
            headers=topic.headers,
            key=message_key,
            # partition=1,
            on_delivery=self.delivery_report,
        )

        self._logger.info("=== Committing transaction at input offset ===")
        self.commit_call.put_nowait(item=True)

        if topic.return_topic is not None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.router.wait_for(topic.return_topic, req_id)
            )

            return result

        return None

    def _commit(self, start_new_transaction: bool = False):
        # Send the consumer's position to transaction to commit
        # them along with the transaction, committing both
        # input and outputs in the same transaction is what provides EOS.
        self.producer.send_offsets_to_transaction(
            self.consumer.position(self.consumer.assignment()),
            self.consumer.consumer_group_metadata(),
        )

        # Commit the transaction
        self.producer.commit_transaction()

        if start_new_transaction:
            self.producer.begin_transaction()

    def _wait_for_commit(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while True:
            while self.commit_call.empty():
                time.sleep(1)
                continue
            result = loop.run_until_complete(self.commit_call.get())
            self._commit(result)

    def create_process(
        self,
        topic: str,
        msg: Message,
        process_input: Callable[[KafkaMessage], None],
    ):
        self._logger.info(
            "=== Processing message at input offset {} ===".format(
                msg.offset()
            )
        )
        try:
            data = str(msg.value().decode())
            json_data: dict = json.loads(data)

        except json.JSONDecodeError as e:
            self._logger.info(f"Error decoding JSON: {e}")

        except Exception as e:
            self._logger.info(f"Error: {e}")

        else:
            headers_data = {}
            if msg.headers() is not None:
                for h in msg.headers():
                    [key, value] = h
                    headers_data[key] = value.decode()

            key = None
            if msg.key() is not None:
                key = msg.key().decode()

            process_input(
                KafkaMessage(
                    topic=topic,
                    key=key,
                    headers=headers_data,
                    payload=json_data,
                )
            )

    def _close(self):
        self._logger.info("=== Commit transaction and close consumer ===")
        self._commit()
        self.consumer.close()

    def create_topic(self, topic_name: str):
        """Create topics"""

        new_topics = [
            NewTopic(topic_name, num_partitions=3, replication_factor=1)
        ]
        # Call create_topics to asynchronously create topics, a dict
        # of <topic,future> is returned.
        fs = self.admin_client.create_topics(new_topics)

        # Wait for operation to finish.
        # Timeouts are preferably controlled by passing request_timeout=15.0
        # to the create_topics() call.
        # All futures will finish at the same time.
        for topic, f in fs.items():
            try:
                f.result()  # The result itself is None
                self._logger.info("Topic {} created".format(topic))
            except Exception as e:
                self._logger.info(
                    "Failed to create topic {}: {}".format(topic, e)
                )

    def list_topics(self) -> List[str]:
        """list topics, groups and cluster metadata"""

        md = self.admin_client.list_topics(timeout=10)

        self._logger.info(
            "Cluster {} metadata (response from broker {}):".format(
                md.cluster_id, md.orig_broker_name
            )
        )

        self._logger.info(" {} brokers:".format(len(md.brokers)))
        for b in iter(md.brokers.values()):
            if b.id == md.controller_id:
                self._logger.info("  {}  (controller)".format(b))
            else:
                self._logger.info("  {}".format(b))

        topics = []
        self._logger.info(" {} topics:".format(len(md.topics)))
        for t in iter(md.topics.values()):
            if t.error is not None:
                errstr = ": {}".format(t.error)
            else:
                errstr = ""

            self._logger.info(
                '  "{}" with {} partition(s){}'.format(
                    t, len(t.partitions), errstr
                )
            )

            # for p in iter(t.partitions.values()):
            #     if p.error is not None:
            #         errstr = ": {}".format(p.error)
            #     else:
            #         errstr = ""

            #     self._logger.info("partition {} leader: {}, replicas: {},"
            #           " isrs: {} errstr: {}".format(p.id, p.leader, p.replicas,
            #                                         p.isrs, errstr))

            topics.append(str(t))

        groups = self.admin_client.list_groups(timeout=10)
        self._logger.info(" {} consumer groups".format(len(groups)))
        for g in groups:
            if g.error is not None:
                errstr = ": {}".format(g.error)
            else:
                errstr = ""

            self._logger.info(
                ' "{}" with {} member(s), protocol: {}, protocol_type: {}{}'.format(
                    g, len(g.members), g.protocol, g.protocol_type, errstr
                )
            )

            # for m in g.members:
            #     self._logger.info("id {} client_id: {} client_host: {}".format(
            #         m.id, m.client_id, m.client_host))

        return topics

    def consume(
        self,
        topics: List[str],
        process_input: Callable[[KafkaMessage], None],
    ):
        try:
            existing_topics = self.list_topics()

            for tp in topics:
                if tp not in existing_topics:
                    self.create_topic(tp)

            # Prior to KIP-447 being supported each input partition requires
            # its own transactional producer, so in this example we use
            # assign() to a single partition rather than subscribe().
            # A more complex alternative is to dynamically create a producer per
            # partition in subscribes rebalanced callback.
            self.consumer.subscribe(topics)

            # def exit_handler():
            #     self._commit()
            #     self.consumer.close()
            #     self.producer.close()

            # atexit.register(exit_handler)

            eof = {}
            msg_cnt = 0
            self._logger.info(
                "=== Starting Consume-Transform-Process loop ==="
            )
            while True:
                # self._logger.info("=== polling === {}".format(datetime.now()))
                # serve delivery reports from previous produce()s
                self.producer.poll(0)

                # read message from input_topic
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                topic, partition = msg.topic(), msg.partition()
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        eof[(topic, partition)] = True
                        self._logger.info(
                            "=== Reached the end of {} [{}] at {}====".format(
                                topic, partition, msg.offset()
                            )
                        )

                        if len(eof) == len(self.consumer.assignment()):
                            self._logger.info("=== Reached end of input ===")
                            # break

                    continue

                # clear EOF if a new message has been received
                eof.pop((topic, partition), None)

                # process message
                self.create_process(topic, msg, process_input)

                msg_cnt += 1
                if msg_cnt >= self._commit_after_received_message_count:
                    self._logger.info(
                        "=== Committing transaction with {} messages at input offset {} ===".format(
                            msg_cnt, msg.offset()
                        )
                    )

                    self.commit_call.put_nowait(item=True)
                    msg_cnt = 0

        finally:
            self._close()