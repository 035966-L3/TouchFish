import time
import socket
import threading
import platform
import sys
import requests
import os
import json
import datetime
import time
import base64
import queue

VERSION = "v4.0.0-prealpha.20"

COLORS = \
{
    "black": 0,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "magenta": 5,
    "cyan": 6,
    "white": 7
}

CONFIG_PATH = "config_client.json"

connection = None
username = ""
ip = ""
port = 0
bell = False
buffer = ""
print_queue = queue.Queue()
blocked = False

def clear_screen():
    if platform.system() == 'Windows':
        os.system('cls')
    if platform.system() != 'Windows':
        os.system('clear')

def dye(text, color_code):
    if color_code:
        return "\033[0m\033[1;3{}m{}\033[8;30m".format(COLORS[color_code], text)
    return text

def prints(text, color_code=None):
    if not blocked:
        while not print_queue.empty():
            print(print_queue.get())
        print(dye(text, color_code))
    if blocked:
        print_queue.put(dye(text, color_code))

clear_screen()
prints("欢迎使用 TouchFish 聊天室客户端！", "yellow")
try:
    newest_version = requests.get("https://www.bopid.cn/chat/newest_version_client.html", timeout=5).content.decode()
except:
    newest_version = "UNKNOWN"
prints("当前版本：{}, 最新版本：{}".format(VERSION, newest_version), "yellow")
prints("请连接聊天室。", "yellow")

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        tmp_config = json.load(f)
        config = {'ip': tmp_config['ip'], 'port': tmp_config['port'], 'username': tmp_config['username'], 'bell': tmp_config['bell']}
        if not config['username']:
            config['username'] = 'user'
except:
    config = {'ip': '127.0.0.1', 'port': 8080, 'username': 'user', 'bell': True}

ip = input("\033[0m\033[1;37m服务器 IP [{}]：".format(config['ip'])).strip()
ip = ip if ip else config['ip']
port = input("\033[0m\033[1;37m端口 [{}]：".format(config['port'])).strip()
port = int(port) if port else config['port']
username = input("\033[0m\033[1;37m用户名 [{}]：".format(config['username'])).strip()
username = username if username else config['username']

prints("正在连接聊天室...", "yellow")
connection = socket.socket()
try:
    connection.connect((ip, port))
    connection.setblocking(False)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
    connection.send(bytes(json.dumps({'type': 'GATE.REQUEST', 'username': username}), encoding="utf-8"))
    time.sleep(3)
except Exception as e:
    prints("连接失败：{}".format(e), "red")
    input()
    sys.exit(1)

if platform.system() == "Windows":
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
    connection.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 180 * 1000, 30 * 1000))
else:
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 180 * 60)
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)

def read():
    global connnection
    global buffer
    while True:
        try:
            chunk = connection.recv(16384).decode('utf-8')
            if not chunk:
                break
            buffer += chunk
        except BlockingIOError:
            break

def get_message():
    global buffer
    message = ""
    while not message:
        try:
            message, buffer = buffer.split('\n', 1)
        except:
            message = ""
    return json.loads(message)

read()

try:
    message = get_message()
    if not message['result'] in ["Accepted", "Pending review", "IP is banned", "Room is full", "Duplicate usernames", "Username consists of banned words"]:
        raise
except:
    prints("连接失败：对方似乎不是 v4 及以上的 TouchFish 服务端。", "red")
    input()
    sys.exit(1)

RESULTS = \
{
    "IP is banned": "您的 IP 被服务端封禁。",
    "Room is full": "服务端连接数已满，无法加入。",
    "Duplicate usernames": "该用户名已被占用，请更换用户名。",
    "Username consists of banned words": "用户名中包含违禁词，请更换用户名。"
}

if message['result'] in ["IP is banned", "Room is full", "Duplicate usernames", "Username consists of banned words"]:
    prints("连接失败：{}".format(RESULTS[message['result']]), "red")
    input()
    sys.exit(1)

if message['result'] == "Accepted":
    prints("连接成功！", "green")

if message['result'] == "Pending review":
    prints("服务端需要对连接请求进行人工审核，请等待...", "white")
    while True:
        try:
            read()
            message = get_message()
            if not message['accepted']:
                prints("服务端拒绝了您的连接请求。", "red")
                prints("连接失败。", "red")
                input()
                sys.exit(1)
            if message['accepted']:
                prints("服务端通过了您的连接请求。", "green")
                prints("连接成功！", "green")
                break
        except:
            pass

config = {'ip': ip, 'port': port, 'username': username, 'bell': bell}

try:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f)
except:
    pass

prints("本次连接中输入的参数已经保存到配置文件 {}，下次连接时将自动加载。".format(CONFIG_PATH), "cyan")
prints("进入聊天室后，按换行符唤醒命令行，输入 help 获取帮助。", "cyan")
prints("5 秒后将进入聊天室...", "cyan")
time.sleep(5)
clear_screen()

CONFIG_LIST = \
"""
参数名称               当前值      修改示例       描述

general.server_ip      {:<12}"192.168.1.1"  服务器 IP
general.server_port    {:<12}12345          服务器端口
general.enter_hint     <1>         "Hi there!\\n"  进入提示

ban.ip                 <2>         ["8.8.8.8"]    IP 黑名单
ban.words              <3>         ["a", "b"]     屏蔽词列表

gate.enter_check       {!s:<12}True           加入是否需要人工放行
gate.max_connections   {:<12}8              最大在线连接数

message.allow_private  {!s:<12}False          是否允许私聊
message.max_length     {:<12}256            最大消息长度（字节）

file.allow_any         {!s:<12}False          是否允许发送文件
file.allow_private     {!s:<12}False          是否允许发送私有文件
file.max_size          {:<12}16384          最大文件大小（字节）

为了防止尖括号处的内容写不下，此处单独列出：
<1>:
{}
<2>:
{}
<3>:
{}
"""[1:-1]

read()
first_data = get_message()
server_version = first_data['server_version']
my_uid = first_data['uid']
config = first_data['config']
users = first_data['users']

def print_message(message):
    first_line = dye("[" + message['time'][11:19] + "]", "black")
    if message['uid'] == my_uid:
        first_line += dye(" [您发送的]", "blue")
    if message['broadcast']:
        first_line += dye(" [广播]", "red")
    if message['private']:
        first_line += dye(" [私聊]", "green")
    first_line += " "
    first_line += dye("@", "black")
    first_line += dye(users[message['uid']], "yellow")
    first_line += dye(":", "black")
    prints(first_line)
    prints(message['content'], "white")

def print_info():
    prints("=" * 70, "black")
    prints("服务端版本：" + server_version, "black")
    prints("您的 UID：" + str(my_uid), "black")
    prints("聊天室参数及具体用户信息详见下表。", "black")
    prints("=" * 70, "black")
    prints(CONFIG_LIST.format(config['general']['server_ip'], config['general']['server_port'], config['gate']['enter_check'], config['gate']['max_connections'], config['message']['allow_private'], config['message']['max_length'], config['file']['allow_any'], config['file']['allow_private'], config['file']['max_size'], config['general']['enter_hint'], config['ban']['ip'], config['ban']['words']), "black")
    prints("=" * 70, "black")
    prints(" UID  状态      用户名", "black")
    for i in range(len(users)):
        prints("{:>4}  {:<10}{}".format(i, users[i]['status'], users[i]['username']), "black")
    prints("=" * 70, "black")

for i in first_data['chat_history']:
    print_message(i)
print_info()
if config['general']['enter_hint']:
    first_line = dye("[" + str(datetime.datetime.now())[11:19] + "]", "black")
    first_line += dye(" [加入提示]", "red")
    first_line += " "
    first_line += dye("@", "black")
    first_line += dye("root", "yellow")
    first_line += dye(":", "black")
    prints(first_line)
    prints(config['general']['enter_hint'], "white")
    
while True:
    input()
