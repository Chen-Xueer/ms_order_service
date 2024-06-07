import asyncio
from typing import Optional
from kafka_app.kafka_management.kafka_topic import KafkaMessage


class KafkaRouter:

    def __init__(self, response_timeout: int = 30):
        self.queue: dict[str, asyncio.Queue] = {}
        self._response_timeout = response_timeout

    def put_message(self, message: KafkaMessage) -> None:
        request_id = message.headers.get("request_id", "")

        queue_id = f"{message.topic}_{request_id}"
        if queue_id in self.queue:
            self.queue[queue_id].put_nowait(message)

    async def wait_for(
        self, return_topic: str, request_id: str
    ) -> KafkaMessage:
        queue_id = f"{return_topic}_{request_id}"
        new_queue = asyncio.Queue(maxsize=1)
        self.queue[queue_id] = new_queue

        try:
            time_sleep = 1
            while new_queue.empty():
                await asyncio.sleep(1)
                time_sleep += 1
                if time_sleep >= self._response_timeout:
                    raise asyncio.TimeoutError

                continue
            response = await new_queue.get()

        except asyncio.TimeoutError:
            del self.queue[queue_id]
            raise Exception(f"kafka response timeout. ref:{queue_id}")

        return response
