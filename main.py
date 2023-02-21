from typing import Dict
from fastapi import FastAPI, BackgroundTasks
from dotenv import load_dotenv
from os import getenv, _exit
from revChatGPT.V1 import Chatbot
from chatgpt import ChatbotContainer, ChatRecord
from feishu import FeishuBot
from feishu_event import EventContainer, FeishuEventType, MessageEvent
from asyncio import sleep, create_task
import json
load_dotenv()

# chatgpt bot与feishu bot的初始化
print("Initializing bot...")
try:
    # gpt bot 配置信息
    config = {}
    config["paid"] = getenv('IS_PLUS', 'false').lower() in ('true', 'yes', '1')
    if getenv('CHAT_ACCESS_TOKEN') is not None or getenv('CHAT_SESSION_TOKEN') is not None:
        print("Using access token or session token.")
        config["access_token"] = getenv('CHAT_ACCESS_TOKEN')
        config["session_token"] = getenv('CHAT_SESSION_TOKEN')
    elif getenv('CHAT_EMAIL') is not None and getenv('CHAT_PASSWORD') is not None:
        print("Using email and password.")
        config["email"] = getenv('CHAT_EMAIL')
        config["password"] = getenv('CHAT_PASSWORD')
    else:
        print("No access token or email and password provided.")
        _exit(1)
    gptbot_container = ChatbotContainer(Chatbot(config=config))
    feishu_bot = FeishuBot(
        getenv("APP_ID", ""),
        getenv("APP_SECRET", ""),
    )
except Exception as e:
    print(e)
    _exit(1)

app = FastAPI()
# 记录飞书用户id和会话id的对应关系
feishu_user_to_conversation_map: Dict[str, ChatRecord] = {}


async def process_conversation(ec: EventContainer):  # 耗时的对话处理任务
    try:
        message_event = MessageEvent.parse_obj(ec.event)
        json_data = json.loads(message_event.message.content)
        if json_data.get('text') is not None:
            message_receive = json_data['text']
            if message_receive == '/reset':
                # 用户指令，重置会话
                record = feishu_user_to_conversation_map.pop(
                    message_event.sender.sender_id.user_id)
                if record is not None:
                    gptbot_container.delete_conversation(
                        record.conversation_id)
                    print(
                        f'reset conversation with {message_event.sender.sender_id.user_id} conversation: {record.conversation_id} pid: {record.parent_id}')
                message_reply = "会话已重置"
            elif message_event.sender.sender_id.user_id not in feishu_user_to_conversation_map:
                # 当前没有关于该用户的记录，开始新会话
                print(
                    f'start new conversation with {message_event.sender.sender_id.user_id}')
                response = await gptbot_container.ask(message_receive)
                chat_record = ChatRecord(
                    response.conversation_id, response.parent_id)
                feishu_user_to_conversation_map[message_event.sender.sender_id.user_id] = chat_record
                message_reply = response.message
            else:
                # 继续已有的会话
                chat_record = feishu_user_to_conversation_map[message_event.sender.sender_id.user_id]
                print(
                    f'continue conversation with {message_event.sender.sender_id.user_id} conversation: {chat_record.conversation_id} pid: {chat_record.parent_id}')
                response = await gptbot_container.ask(message_receive, chat_record.conversation_id, chat_record.parent_id)
                # 更新会话的进度
                chat_record.parent_id = response.parent_id
                chat_record.conversation_id = response.conversation_id
                message_reply = response.message
            # 返回信息给飞书
            await feishu_bot.reply_message(message_reply, message_event.message.message_id)
    except Exception as e:
        print("process_conversation error")
        print(e)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/bot")
async def bot(ec: EventContainer, background_tasks: BackgroundTasks):
    try:
        if (FeishuEventType(ec.header.event_type) is FeishuEventType.ReceiveMessage):
            background_tasks.add_task(process_conversation, ec)
        return ''
    except Exception as e:
        print(e)
        return ''


@app.on_event("startup")
def startup_function():
    create_task(schedule_access_token())


async def schedule_access_token():
    while True:
        await feishu_bot.refresh_access_token()
        await sleep(1800)  # 定时刷新 access token

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
