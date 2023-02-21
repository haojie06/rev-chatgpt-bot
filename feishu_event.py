# 飞书相关的事件定义
from typing import List
from typing import Any
from pydantic import BaseModel, create_model
from enum import Enum


class FeishuEventType(Enum):
    ReceiveMessage = "im.message.receive_v1"


class Header(BaseModel):
    event_id: str
    event_type: str
    create_time: str
    token: str
    app_id: str
    tenant_key: str


class Id(BaseModel):
    union_id: str
    user_id: str
    open_id: str


class Mention(BaseModel):
    key: str
    id: Id
    name: str
    tenant_key: str


class Message(BaseModel):
    message_id: str
    root_id: str | None
    parent_id: str | None
    create_time: str
    chat_id: str
    chat_type: str
    message_type: str
    content: str
    mentions: List[Mention] | None


class SenderId(BaseModel):
    union_id: str
    user_id: str
    open_id: str


class Sender(BaseModel):
    sender_id: SenderId
    sender_type: str
    tenant_key: str


class MessageEvent(BaseModel):
    sender: Sender
    message: Message

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)


def event_container_factory(event_type_str: str) -> Any:
    event_type = FeishuEventType(event_type_str)
    if event_type is FeishuEventType.ReceiveMessage:
        return create_model('MessageEventContainer', header=(Header, ...), event=(MessageEvent, ...))
    else:
        raise ValueError(f'Unknown event type: {event_type}')


class EventContainer(BaseModel):
    header: Header
    event: Any

    @classmethod
    def create(cls, event_type: str, header: Header, data: dict) -> 'EventContainer':
        EventClass = event_container_factory(event_type)
        return cls(header=header, event=EventClass.parse_obj(data))
