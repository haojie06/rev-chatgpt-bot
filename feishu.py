import aiohttp
import json


class FeishuBot:
    access_token: str

    app_id: str

    app_secret: str

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret

    # 刷新 access_token
    async def refresh_access_token(self):
        """Refresh access token
        """
        url = f"https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"app_id": self.app_id, "app_secret": self.app_secret}) as response:
                if response.status == 200:
                    json = await response.json()
                    access_token = json.get("app_access_token")
                    print(f"New Feishu Access Token: {access_token}")
                    self.feishu_access_token = access_token
                else:
                    print(
                        f"Error getting access token, status code: {response.status}")

    async def reply_message(self, message: str, message_id: str):
        """Reply feishu message

        Args:
            message (str): message content to reply
            message_id (str): reply to which message
        """
        async with aiohttp.ClientSession() as session:
            response_body = ""
            async with session.post(
                url=f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.feishu_access_token}",
                },
                json={
                    "content": json.dumps({"text": message}),
                    "msg_type": "text"
                }
            ) as response:
                try:
                    response_body = await response.text()
                    response_obj = json.loads(response_body)
                    result_code = response_obj.get("code")
                    if result_code != 0:
                        print(
                            f"{response.url} Reply message failed [{result_code}]: {response_obj['msg']}")
                except json.JSONDecodeError as e:
                    print(f"Error parsing response: {response_body}")
                except Exception as e:
                    print(f"Error: {e}")
