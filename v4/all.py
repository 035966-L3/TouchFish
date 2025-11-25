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

VERSION = "v4.0.0-alpha.2"

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

DEFAULT_CLIENT_CONFIG = {"side": "Client", "ip": "127.0.0.1", "port": 8080, "username": "user"}

DEFAULT_SERVER_CONFIG = \
{
    "side": "Server",
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

def announce(uid):
    first_line = dye("[" + str(datetime.datetime.now())[11:19] + "]", "black")
    if uid == my_uid:
        first_line += dye(" [您发送的]", "blue")
    first_line += dye(" [公告]", "red")
    first_line += " "
    first_line += dye("@", "black")
    first_line += dye(users[uid]['username'], "yellow")
    first_line += dye(":", "black")
    prints(first_line)

def print_message(message):
    first_line = dye("[" + message['time'][11:19] + "]", "black")
    if message['from'] == my_uid:
        first_line += dye(" [您发送的]", "blue")
    if message['to'] == my_uid and my_uid:
        first_line += dye(" [发给您的]", "blue")
    if message['to'] == -1:
        first_line += dye(" [广播]", "red")
    if message['to'] >= 1:
        first_line += dye(" [私聊]", "green")
    first_line += " "
    first_line += dye("@", "black")
    first_line += dye(users[message['from']]['username'], "yellow")
    if message['to'] >= 1:
        first_line += dye(" -> ", "green")
        first_line += dye("@", "black")
        first_line += dye(users[message['to']]['username'], "yellow")
    first_line += dye(":", "black")
    prints(first_line)
    prints(message['content'], "white")

def print_info():
    printf("=" * 70, "black")
    printf("服务端版本：" + server_version, "black")
    printf("您的 UID：" + str(my_uid), "black")
    printf("聊天室参数及具体用户信息详见下表。", "black")
    printf("=" * 70, "black")
    printf(CONFIG_LIST.format(config['general']['server_ip'], config['general']['server_port'], config['gate']['enter_check'], config['gate']['max_connections'], config['message']['allow_private'], config['message']['max_length'], config['file']['allow_any'], config['file']['allow_private'], config['file']['max_size'], config['general']['enter_hint'], config['ban']['ip'], config['ban']['words']), "black")
    printf("=" * 70, "black")
    if 'ip' in users[0]:
        printf(" UID  IP                        状态      用户名", "black")
        for i in range(len(users)):
            printf("{:>4}  {:<26}{:<10}{}".format(i, "{}:{}".format(users[i]['ip'][0], users[i]['ip'][1]), users[i]['status'], users[i]['username']), "black")
    else:
        printf(" UID  状态      用户名", "black")
        for i in range(len(users)):
            printf("{:>4}  {:<10}{}".format(i, users[i]['status'], users[i]['username']), "black")
    printf("=" * 70, "black")

config = DEFAULT_SERVER_CONFIG

try:
    with open("config.json", "r", encoding="utf-8") as f:
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
                    for element in tmp_object:
                        if not isinstance(element, str):
                            raise
                    if len(tmp_object) != len(set(tmp_object)):
                        raise
                if item == "ban.words":
                    for element in tmp_object:
                        if '\n' in element or '\r' in element or not element:
                            raise
                if item == "ban.ip":
                    for element in tmp_object:
                        if not check_ip(element):
                            raise
                if item == "general.server_ip" and not check_ip(tmp_object):
                    raise
                if item == "general.server_port" and tmp_object >= 65536:
                    raise
            config = tmp_config
        if tmp_config['side'] == "Client":
            if not isinstance(tmp_config['ip'], str):
                raise
            if not isinstance(tmp_config['port'], int):
                raise
            if not isinstance(tmp_config['username'], str):
                raise
            if int(tmp_config['port']) >= 65536:
                raise
            if tmp_config['username'] in ["", "root"]:
                raise
            if not check_ip(tmp_config['ip']):
                raise
            config = tmp_config
except:
    config = DEFAULT_CLIENT_CONFIG

EXIT_FLAG = False
blocked = False
my_uid = 0
users = []

clear_screen()
prints("欢迎使用 TouchFish 聊天室！", "yellow")
prints("当前程序版本：{}".format(VERSION), "yellow")
tmp_side = input("\033[0m\033[1;37m启动类型 (Server = 服务端, Client = 客户端) [{}]：".format(config['side']))
if not tmp_side in ["Server", "Client"]:
    prints("参数错误。", "red")
    input()
    sys.exit(1)

if tmp_side == "Server":
    if config['side'] == "Client":
        config = DEFAULT_SERVER_CONFIG
    tmp_ip = input("\033[0m\033[1;37m服务器 IP [{}]：".format(config['general']['server_ip']))
    if not tmp_ip:
        tmp_ip = config['general']['server_ip']
    config['general']['server_ip'] = tmp_ip
    if not check_ip(tmp_ip):
        prints("参数错误。", "red")
        input()
        sys.exit(1)
    tmp_port = input("\033[0m\033[1;37m端口 [{}]：".format(config['general']['server_port']))
    if not tmp_port:
       tmp_port = config['general']['server_port']
    try:
        tmp_port = int(tmp_port)
        if tmp_port <= 0 or tmp_port >= 65536:
            raise
    except:
        prints("参数错误。", "red")
        input()
        sys.exit(1)
    config['general']['server_port'] = tmp_port
    tmp_max_connections = input("\033[0m\033[1;37m最大连接数 [{}]：".format(config['gate']['max_connections']))
    if not tmp_max_connections:
       tmp_max_connections = config['gate']['max_connections']
    try:
        tmp_max_connections = int(tmp_max_connections)
        if tmp_max_connections <= 0 or tmp_max_connections >= 4294967297:
            raise
    except:
        prints("参数错误。", "red")
        input()
        sys.exit(1)
    config['gate']['max_connections'] = tmp_max_connections
    
    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f)
    except:
        prints("启动时遇到错误：参数 config.json 保存失败。", "red")
        input()
        sys.exit(1)
    try:
        with open("log.txt", "w", encoding="utf-8") as f:
            json.dump(config, f)
    except:
        prints("启动时遇到错误：无法向日志文件 log.txt 写入内容。", "red")
        input()
        sys.exit(1)
    
    try:
        s = socket.socket()
        s.bind((config['general']['server_ip'], config['general']['server_port']))
        s.listen(config['gate']['max_connections'])
        s.setblocking(False)
    except:
        print("启动时遇到错误：无法在给定的地址上启动 socket，请检查 IP 地址或更换端口。")
        input()
        sys.exit(1)

    users = [{"body": None, "extra": None, "buffer": "", "ip": (config['general']['server_ip'], config['general']['server_port']), "username": "root", "status": "Root"}]

    with open("./log.txt", "a", encoding="utf-8") as file:
        file.write(json.dumps({'type': 'SERVER.START', 'time': time_str(), 'server_version': VERSION, 'config': config}) + "\n")

if tmp_side == "Client":
    pass # test
    