from datetime import datetime, timedelta
import json
import logging
import uuid
import threading
from confluent_kafka import (
    Producer,
    Consumer,
    KafkaError,
    Message,
    TopicPartition,
)
from typing import Dict, Optional
from kafka_app.kafka_management.kafka_topic import KafkaMessage, Topic
from typing import List, Callable
from confluent_kafka.admin import AdminClient, NewTopic


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
        new_topic_config: dict,
        sasl_username: Optional[str] = None,
        sasl_password: Optional[str] = None,
        sasl_mechanism: str = "SCRAM-SHA-512",
        security_protocol: str = "SASL_SSL",
        _response_timeout: int = 30,
        _logger=logger,
    ):
        self.service_name = service_name

        # new topic config
        if (
            "num_partitions" in new_topic_config
            and "replication_factor" in new_topic_config
        ):
            self.new_topic_config = new_topic_config
        else:
            raise ValueError(
                "num_partitions and replication_factor are required in new_topic_config"
            )

        self.basic_config = {
            "bootstrap.servers": brokers,
        }
        if sasl_username is not None and sasl_password is not None:
            self.basic_config = {
                "bootstrap.servers": brokers,
                "sasl.mechanisms": sasl_mechanism,
                "security.protocol": security_protocol,
                "sasl.username": sasl_username,
                "sasl.password": sasl_password,
            }
        # Admin
        self.admin_client = AdminClient(self.basic_config)

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
            # fallback broker version if ApiVersionRequest fails
            "broker.version.fallback": "3.6.1",
            # broker address family: v4, v6, or any
            "broker.address.family": "v4",
            # heartbeat to ensure consumer's session stays active
            "heartbeat.interval.ms": "3000",
        }
        consumer_config.update(self.basic_config)
        self.consumer = Consumer(consumer_config)
        self.consumer_config = consumer_config
        self.consumer_active = False
        self.topic_producer = None

        # Producers dict
        self.producers: Dict[str, Producer] = {}
        self.response_timeout = _response_timeout
        self.commit_lock = []

        # General producer
        self.general_producer = Producer(self.basic_config)

        # Logger
        self._logger = _logger

    def _delivery_report(self, err, msg):
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

        worker = self.general_producer
        if self.topic_producer is not None:
            worker = self.producers[self.topic_producer]

        def produce():
            worker.produce(
                topic=topic.name,
                value=json.dumps(topic.data).encode(),
                headers=topic.headers,
                key=message_key,
                on_delivery=self._delivery_report,
            )

        if topic.return_topic is not None:
            result = self._return_consume(topic.return_topic, req_id, produce)

            self._logger.info(
                f"=== Return message: {result.key} {result.topic} {result.headers} {json.dumps(result.payload)} ==="
            )
            return result

        else:
            produce()

        return None

    def _start_commit(self, p_key):

        try:
            if not self.consumer_active:
                raise RuntimeError("Consumer is not active")

            if p_key not in self.producers:
                raise RuntimeError(f"Producer {p_key} not found")

            if p_key in self.commit_lock:
                return

            self.topic_producer = None
            self.commit_lock.append(p_key)

            work_producer = self.producers[p_key]

            key_data = p_key.split("-")

            consume_topic = key_data[1]
            consume_partition = int(key_data[2])

            # Send the consumer's position to transaction to commit
            # them along with the transaction, committing both
            # input and outputs in the same transaction is what provides EOS.

            work_producer.send_offsets_to_transaction(
                self.consumer.position(
                    [
                        TopicPartition(
                            topic=consume_topic, partition=consume_partition
                        )
                    ]
                ),
                self.consumer.consumer_group_metadata(),
            )

            # Commit the transaction
            work_producer.commit_transaction()

        except Exception as e:
            self._logger.error(f"Commit Error: {e}")

        finally:
            if p_key in self.commit_lock:
                self.commit_lock.remove(p_key)

    def _payload_to_kafka_message(
        self,
        topic: str,
        msg: Message,
    ) -> Optional[KafkaMessage]:
        self._logger.info(
            "=== Processing message at input offset {} ===".format(
                msg.offset()
            )
        )
        try:
            data = str(msg.value().decode())
            json_data: dict = json.loads(data)

        except json.JSONDecodeError as e:
            self._logger.error(f"Error decoding JSON: {e}")

        except Exception as e:
            self._logger.error(f"Payload to Kafka Message Error: {e}")

        else:
            headers_data = {}
            if msg.headers() is not None:
                for h in msg.headers():
                    [key, value] = h
                    headers_data[key] = value.decode()

            key = None
            if msg.key() is not None:
                key = msg.key().decode()

            message = KafkaMessage(
                topic=topic,
                key=key,
                headers=headers_data,
                payload=json_data,
            )

            return message

    def close(self):
        self._logger.info("=== Flush producers ===")

        for ptid in self.producers.keys():
            self.producers[ptid].flush()

        self._logger.info("=== Close consumer ===")
        self.consumer.close()

    def _create_topic(self, topic_name: str):
        """Create topics"""

        new_topics = [
            NewTopic(
                topic_name,
                num_partitions=self.new_topic_config["num_partitions"],
                replication_factor=self.new_topic_config["replication_factor"],
            )
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
                self._logger.error(
                    "Failed to create topic {}: {}".format(topic, e)
                )

    def _list_topics(self, logging: bool = True) -> List[str]:
        """list topics, groups and cluster metadata"""

        md = self.admin_client.list_topics(timeout=10)

        topics = []
        for t in iter(md.topics.values()):
            if t.error is not None:
                errstr = ": {}".format(t.error)
            else:
                errstr = ""

            if logging:
                self._logger.info(
                    '  "{}" with {} partition(s){}'.format(
                        t, len(t.partitions), errstr
                    )
                )

            topics.append(str(t))

        return topics

    def _return_consume(
        self, return_topic: str, request_id: str, produce: Callable[[], None]
    ) -> KafkaMessage:

        return_consumer_config = self.consumer_config.copy()
        return_consumer_config.update(
            {
                "group.id": f"{self.service_name}-{request_id}",
                "auto.offset.reset": "latest",
                "enable.auto.commit": True,
            }
        )
        return_consumer = Consumer(return_consumer_config)

        existing_topics = self._list_topics(logging=False)
        if return_topic not in existing_topics:
            self._create_topic(return_topic)

        return_consumer.subscribe([return_topic])

        try:
            message_sent = False
            datetime_now = datetime.now()
            datetime_timeout = datetime_now + timedelta(
                seconds=self.response_timeout
            )
            while datetime_now < datetime_timeout:
                datetime_now = datetime.now()
                msg = return_consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                topic, partition = msg.topic(), msg.partition()
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        self._logger.info(
                            "=== Reached the end of {} [{}] at {}====".format(
                                topic, partition, msg.offset()
                            )
                        )
                        if not message_sent:
                            produce()
                            message_sent = True

                        if self.topic_producer is not None:
                            self._start_commit(self.topic_producer)

                    continue

                data = self._payload_to_kafka_message(topic, msg)

                if (
                    data is not None
                    and data.headers["request_id"] == request_id
                ):
                    return data

            raise RuntimeError("Timeout waiting for return message")

        except Exception as e:
            self._logger.error(f"Return Consume Error: {e}")
            raise e

        finally:
            # Close down consumer to commit final offsets.
            return_consumer.close()

    def _consumer_on_assign(self, consumer, partitions: List[TopicPartition]):

        for part in partitions:
            topic = part.topic
            partition_assign = part.partition

            # Producer
            producer_key = (
                f"{self.service_name}-{topic}-{str(partition_assign)}"
            )
            producer_config = {
                "transactional.id": producer_key,
                "broker.version.fallback": "3.6.1",
                "broker.address.family": "v4",
            }
            producer_config.update(self.basic_config)
            self.producers[producer_key] = Producer(producer_config)

            # Init transactions
            self.producers[producer_key].init_transactions()

    def consume(
        self,
        topics: List[str],
        process_input: Callable[[KafkaMessage], None],
    ):

        if len(topics) == 0:
            self._logger.info("No topics to consume")
            return

        existing_topics = self._list_topics()

        for tp in topics:
            if tp not in existing_topics:
                self._create_topic(tp)

        self.consumer.subscribe(topics, on_assign=self._consumer_on_assign)

        try:
            eof = {}
            self._logger.info(
                "=== Starting Consume-Transform-Process loop ==="
            )
            self.consumer_active = True
            while self.consumer_active:

                # serve delivery reports from previous produce()s
                for ptid in self.producers.keys():
                    self.producers[ptid].poll(0)

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

                    continue

                # clear EOF if a new message has been received
                eof.pop((topic, partition), None)

                producer_key = f"{self.service_name}-{topic}-{str(partition)}"
                self.producers[producer_key].begin_transaction()
                self.topic_producer = producer_key

                # process message
                message = self._payload_to_kafka_message(topic, msg)

                if message is not None:
                    process_input(message)

                self._start_commit(producer_key)

        except Exception as e:
            self.consumer_active = False
            self._logger.error(f"Error: {str(e)}")
            if "Consumer closed" not in str(e):
                self.consumer.close()