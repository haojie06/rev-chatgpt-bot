from typing import Union
from revChatGPT.V1 import Chatbot
from asyncio import Lock


# 记录会话的类
class ChatRecord:
    def __init__(self, conversation_id: str, parent_id: str):
        self.conversation_id = conversation_id
        self.parent_id = parent_id


class ChatResponse:
    message: str

    conversation_id: str

    parent_id: str

    def __init__(self, message: str, conversation_id: str, parent_id: str):
        self.message = message
        self.conversation_id = conversation_id
        self.parent_id = parent_id


class ChatbotContainer:
    def __init__(self, gptbot: Chatbot):
        self.chatbot = gptbot
        self.lock = Lock()
        self.feishu_access_token = ""

    async def ask(self, prompt: str, conversation_id: Union[str, None] = None, parent_id: Union[str, None] = None):
        async with self.lock:
            # 当前 revChatGPT还未支持异步调用，所以这里依旧会阻塞主线程
            if conversation_id is None:
                self.chatbot.reset_chat()
                response = [msg for msg in self.chatbot.ask(
                    prompt, conversation_id=conversation_id, parent_id=parent_id)][-1]
            else:
                response = [msg for msg in self.chatbot.ask(prompt)][-1]
            return ChatResponse(response['message'], response['conversation_id'], response['parent_id'])

    def delete_conversation(self, conversation_id: str):
        self.chatbot.delete_conversation(conversation_id)
