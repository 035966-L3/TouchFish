import base64
import cmd
import datetime
import json
import os
import platform
import queue
import re
import requests
import socket
import sys
import threading
import time

VERSION = "v4.0.0-alpha.1"

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

CONFIG_PATH = "config.json"

DEFAULT_CLIENT_CONFIG = {"ip": "127.0.0.1", "port": 8080, "username": "user"}

DEFAULT_SERVER_CONFIG = \
{
    "general": {"server_ip": "127.0.0.1", "server_port": 8080, "enter_hint": ""},
    "ban": {"ip": [], "words": []},
    "gate": {"enter_check": False, "max_connections": 256},
    "message": {"allow_private": True, "max_length": 16384},
    "file": {"allow_any": True, "allow_private": True, "max_size": 4294967296}
}

CONFIG_TYPE_CHECK_TABLE = \
{
    "general.server_ip": "str", "general.server_port": "int", "general.enter_hint": "str",
    "ban.ip": "list", "ban.words": "list",
    "gate.enter_check": "bool", "gate.max_connections": "int",
    "message.allow_private": "bool", "message.max_length": "int",
    "file.allow_any": "bool", "file.allow_private": "bool", "file.max_size": "int" 
}

CONFIG_HINT = \
"""
修改命令格式示例：general.server_ip "192.168.1.1"
修改命令的输入数据格式以下表给出的修改示例（而非当前值）为准。
请注意，查询命令的输出数据格式与此不尽相同。
输入 done 以结束配置。
"""

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

"""

WEBPAGE_CONTENT = \
"""
HTTP/1.1 405 Method Not Allowed
Content-Type: text/html; charset=utf-8
Connection: close

<html><head><meta name="color-scheme" content="light dark"></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">
您似乎正在使用浏览器或类似方法向 TouchFish Server 发送请求。
此类请求可能会危害 TouchFish Server 的正常运行，因此请不要继续使用此访问方法，否则我们可能会封禁您的 IP。
正确的访问方法是，使用 TouchFish 生态下任意兼容的 TouchFish Client 登录 TouchFish Server。
欲了解更多有关 TouchFish 聊天室的信息，请访问 TouchFish 聊天室的官方 Github 仓库：
https://github.com/2044-space-elevator/TouchFish

Seemingly you are sending requests to TouchFish Server via something like Web browsers.
Such requests are HAZARDOUS to the server and will result in a BAN if you insist on this access method.
To use the TouchFish chatroom service correctly, you might need a dedicated TouchFish Client.
For more information, please visit the official Github repository of this project:
https://github.com/2044-space-elevator/TouchFish
</pre></body></html>
"""[1:]

def clear_screen():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def dye(text, color_code):
    if color_code:
        return "\033[0m\033[1;3{}m{}\033[8;30m".format(COLORS[color_code], text)
    return text

def flush():
    global print_queue
    if not blocked:
        while not print_queue.empty():
            print(print_queue.get())

def prints(text, color_code=None):
    global print_queue
    if not blocked:
        print(dye(text, color_code))
    if blocked:
        print_queue.put(dye(text, color_code))

def printf(text, color_code=None):
    print(dye(text, color_code))

def check_ip_segment(element):
    if not '/' in element:
        element = element + "/32"
    pattern = r'^(\d+)\.(\d+)\.(\d+)\.(\d+)/(\d+)$'
    match = re.search(pattern, element)
    if not match:
        return []
    for i in range(1, 5):
        if int(match.group(i)) < 0 or int(match.group(i)) > 255:
            return []
    if int(match.group(5)) < 0 or int(match.group(5)) > 32:
        return []
    if int(match.group(5)) < 24:
        return [""]
    if int(match.group(4)) % 2 ** (32 - int(match.group(5))):
        return []
    result = []
    for i in range(int(match.group(4)), int(match.group(4)) + 2 ** (32 - int(match.group(5)))):
        result.append("{}.{}.{}.{}".format(int(match.group(1)), int(match.group(2)), int(match.group(3)), i))
    return result

def check_ip(element):
    pattern = r'^(\d+)\.(\d+)\.(\d+)\.(\d+)$'
    match = re.search(pattern, element)
    if not match:
        return False
    for i in range(1, 5):
        if int(match.group(i)) < 0 or int(match.group(i)) > 255:
            return False
    return True

def time_str():
    return str(datetime.datetime.now())

side = "Server"
config = DEFAULT_SERVER_CONFIG

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        tmp_config = json.load(f)
        if not tmp_config['side'] in ["Server", "Client"]:
            raise
        if tmp_config['side'] == "Server":
            for item, type in CONFIG_TYPE_CHECK_TABLE.items():
                first, second = item.split('.')
                tmp_object = tmp_config[first][second]
                if not eval("isinstance(tmp_object, {})".format(type)):
                    raise
                if type == "int" and tmp_object <= 0 or type == "int" and tmp_object >= 4294967297:
                    raise
                if type == "list":
                    for item in tmp_object:
                        if not isinstance(item, str):
                            raise
            # ...
            config = tmp_config
        if tmp_config['side'] == "Client":
            # ...
            config = tmp_config

# ...
