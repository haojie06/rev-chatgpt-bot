FROM python:3.11

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 记得配置.env文件，或者指定环境变量
COPY . .
CMD [ "python", "./main.py" ]