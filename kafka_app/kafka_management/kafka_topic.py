from typing import Optional


class Topic:
    def __init__(
        self,
        name: str,
        data: dict,
        headers: Optional[dict] = None,
        return_topic: Optional[str] = None,
    ) -> None:
        if headers is None:
            headers = {}

        self.name = name
        self.data = data
        self.headers = headers
        self.return_topic = return_topic


class KafkaMessage:
    def __init__(
        self, topic: str, headers: dict, payload: dict, key: Optional[str]
    ):
        self.topic = topic
        self.key = key
        self.headers = headers
        self.payload = payload
