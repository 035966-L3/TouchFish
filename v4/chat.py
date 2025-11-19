import socket
import platform
import re
import cmd
import datetime
import threading
import time
import sys
import json
import base64
import queue
import os
import tabulate
import requests
from random import randint

# 版本
VERSION = "v4.0.0-prealpha.1"


config = \
{
    "general": { "server_ip": "0.0.0.0", "server_port": 8080, "enter_hint": "" },
    "ban": { "ip": [], "words": [] },
    "join": { "enter_check": False, "max_connections": 256 },
    "message": { "allow_private": True, "max_length": 16384 },
    "file": { "allow_any": True, "allow_private": True, "max_size": 4294967296 }
}

CONFIG_PATH = "config.json"

CONFIG_TYPE_CHECK_TABLE = \
{
    "general.server_ip": "str", "general.server_port": "int", "general.enter_hint": "str",
    "ban.ip": "list", "ban.words": "list",
    "join.enter_check": "bool", "join.max_connections": "int",
    "message.allow_private": "bool", "message.max_length": "int",
    "file.allow_any": "bool", "file.allow_private": "bool", "file.max_size": "int" 
}

CONFIG_HINT = \
"""
系统没有检测到合法的配置文件，请根据下表手动指定参数。
命令示例：general.server_ip "192.168.1.1"
输入 done 以结束配置。
未指定的参数将使用默认值。

参数名称               默认值      修改示例       描述

general.server_ip      "0.0.0.0"   "192.168.1.1"  服务器 IP
general.server_port    8080        12345          服务器端口
general.enter_hint     ""          "Hi there!"    进入提示

ban.ip                 []          ["8.8.8.8"]    封禁的 IP 列表
ban.words              []          ["a", "b"]     屏蔽词列表

join.enter_check       False       True           加入是否需要人工放行
join.max_connections   256         8              最大在线连接数

message.allow_private  True        False          是否允许私聊
message.max_length     16384       256            最大消息长度（字节）

file.allow_any         True        False          是否允许发送文件
file.allow_private     True        False          是否允许发送私有文件
file.max_size          4294967296  16384          最大文件大小（字节）
"""

try:
    with open(CONFIG_PATH, "r") as f:
        tmp_config = json.load(f)
        for item, type in CONFIG_TYPE_CHECK_TABLE.items():
            first, second = item.split('.')
            tmp_object = tmp_config[first][second]
            if not eval("isinstance(tmp_object, {})".format(type)):
                raise
            if type == "int" and tmp_object <= 0:
                raise
            if type == "list":
                for item in tmp_object:
                    if not isinstance(item, str):
                        raise
        config = tmp_config
    print("检测到合法的配置文件：{}".format(CONFIG_PATH))
    print("加载成功！")
except:
    print(CONFIG_HINT)
    while True:
        try:
            command = input()
            if command == "done":
                break
            key, value = command.split(' ', 1)
            if not key in CONFIG_TYPE_CHECK_TABLE:
                raise
            if not eval("isinstance({}, {})".format(value, CONFIG_TYPE_CHECK_TABLE[key])):
                raise
            if CONFIG_TYPE_CHECK_TABLE[key] == "int" and int(value) <= 0:
                raise
            if CONFIG_TYPE_CHECK_TABLE[key] == "list":
                for item in eval(value):
                    if not isinstance(item, str):
                        raise
            first, second = key.split('.')
            config[first][second] = eval(value)
            print("设置成功。")
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print("输入不正确，请重试。")
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)
        print("参数已经成功保存到配置文件 {}，下次启动时将自动加载配置项。".format(CONFIG_PATH))
    except:
        print("警告：无法将参数保存到配置文件 {}，请在聊天室启动后输入 save 重试。".format(CONFIG_PATH))

print("正在启动 TouchFish 聊天室...")
print()

def time_str() -> str:
    return "\"" + str(datetime.datetime.now()) + "\""

s = socket.socket()
try:
    s.bind((config['general']['server_ip'], config['general']['server_port']))
except Exception as err:
    print("[Error] 绑定端口失败，可能的原因有：\n1. 端口已被占用\n2. 没有权限绑定该端口\n错误信息：\n" + str(err))
    exit()
s.listen(config['join']['max_connections'])
s.setblocking(False)

try:
    NEWEST_VERSION = requests.get("https://bopid.cn/chat/newest_version_chat.html").content.decode()
except:
    NEWEST_VERSION = "UNKNOWN"

with open("./log.txt", "a") as file:
    file.write(r'{{ type: "MISC.SERVER_START", time: {}, config: {} }}'.format(time_str(), json.dumps(config)) + "\n")

# --------------------- 此分界线以下的内容等待施工。 ---------------------
