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
import subprocess

VERSION = "v4.0.0-prealpha.18"

COLORS = \
{
    "black": 0,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "pink": 5,
    "cyan": 6,
    "white": 7
}

def get_hh_mm_ss() -> str:
    """
    return HH:MM:SS
    like 11:45:14
    """
    return datetime.datetime.now().strftime("%H:%M:%S")

def clear_screen():
    """清屏"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def print_colored(text, color_code):
    """打印带颜色的文本"""
    print("\033[3{}m{}\033[0m".format(COLORS[color_code], text))

def print_highlight_colored(text, color_code):
    """打印带颜色的高亮文本"""
    print("\033[1;3{}m{}\033[0m".format(COLORS[color_code], text))

connection = None
username = ""
ip = ""
port = 0
bell = False
buffer = ""
        
clear_screen()
print_highlight_colored("欢迎使用 TouchFish 聊天室客户端！", "yellow")
try:
    newest_version = requests.get("https://www.bopid.cn/chat/newest_version_client.html", timeout=5).content.decode()
except:
    newest_version = "UNKNOWN"
print_highlight_colored("当前版本：{}, 最新版本：{}".format(VERSION, newest_version), "yellow")
print_highlight_colored("请连接聊天室。", "yellow")

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        tmp_config = json.load(f)
        config = {'ip': tmp_config['ip'], 'port': tmp_config['port'], 'username': tmp_config['username'], 'bell': tmp_config['bell']}
        if not config['username']:
            config['username'] = 'user'
except:
    config = {'ip': '127.0.0.1', 'port': 8080, 'username': 'user', 'bell': True}

ip = input("服务器 IP [{}]：".format(config['ip'])).strip()
ip = ip if ip else config['ip']
port = input("端口 [{}]：".format(config['port'])).strip()
port = int(port) if port else config['port']
username = input("用户名 [{}]：".format(config['username'])).strip()
username = username if username else config['username']

print_highlight_colored("正在连接聊天室...", "yellow")
connection = socket.socket()
try:
    connection.connect((ip, port))
    connection.setblocking(False)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
    connection.send(bytes(json.dumps({'type': 'GATE.REQUEST', 'username': username}), encoding="utf-8"))
    time.sleep(3)
except Exception as e:
    print_highlight_colored("连接失败：{}".format(e), "red")
    input()
    sys.exit(1)

if platform.system() == "Windows":
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
    connection.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 180 * 1000, 30 * 1000))
else:
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 180 * 60)
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)

while True:
    try:
        chunk = connection.recv(16384).decode('utf-8')
        if not chunk:
            break
        buffer += chunk
    except BlockingIOError:
        break

try:
    message, buffer = buffer.split('\n', 1)
    message = json.loads(message)
    if not message['result'] in ["Accepted", "Pending review", "IP is banned", "Room is full", "Duplicate usernames", "Username consists of banned words"]:
        raise
except:
    print_highlight_colored("连接失败：对方似乎不是 v4 及以上的 TouchFish 服务端。", "red")
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
    print_highlight_colored("连接失败：{}".format(RESULTS[message['result']]), "red")
    input()
    sys.exit(1)

if message['result'] == "Accepted":
    print_highlight_colored("连接成功！", "green")

if message['result'] == "Pending review":
    print_highlight_colored("服务端需要对连接请求进行人工审核，请等待...", "white")
    while True:
        try:
            while True:
                try:
                    chunk = connection.recv(16384).decode('utf-8')
                    if not chunk:
                        break
                    buffer += chunk
                except BlockingIOError:
                    break
            message, buffer = buffer.split('\n', 1)
            message = json.loads(message)
            if not message['accepted']:
                print_highlight_colored("服务端拒绝了您的连接请求。", "red")
                print_highlight_colored("连接失败。", "red")
                input()
                sys.exit(1)
            if message['accepted']:
                print_highlight_colored("服务端通过了您的连接请求。", "green")
                print_highlight_colored("连接成功！", "green")
                break
        except:
            pass

print_highlight_colored("3 秒后将进入聊天室...", "green")
time.sleep(3)
clear_screen()

config = {'ip': ip, 'port': port, 'username': username, 'bell': bell}

try:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f)
except:
    pass

while True:
    pass # test
