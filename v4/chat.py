import socket
import platform
import cmd
import datetime
import threading
import time
import sys
import json
import base64
import queue
import os
import requests
from random import randint

# 版本
VERSION = "v4.0.0-prealpha.7"

config = \
{
    "general": {"server_ip": "0.0.0.0", "server_port": 8080, "enter_hint": ""},
    "ban": {"ip": [], "words": []},
    "join": {"enter_check": False, "max_connections": 256},
    "message": {"allow_private": True, "max_length": 16384},
    "file": {"allow_any": True, "allow_private": True, "max_size": 4294967296}
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
"""

CONFIG_LIST = \
"""
参数名称               默认值      修改示例       描述

general.server_ip      "0.0.0.0"   "192.168.1.1"  服务器 IP
general.server_port    8080        12345          服务器端口
general.enter_hint     ""          "Hi there!\n"  进入提示

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
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
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
except:
    print(CONFIG_HINT)
    print(CONFIG_LIST)
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
            print("输入格式不正确，请重试。")
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f)
        print("参数已经成功保存到配置文件 {}，下次启动时将自动加载配置项。".format(CONFIG_PATH))
    except:
        print("警告：无法将参数保存到配置文件 {}，请在聊天室启动后输入 save 重试。".format(CONFIG_PATH))
    print()

try:
    NEWEST_VERSION = requests.get("https://bopid.cn/chat/newest_version_chat.html", timeout=3).content.decode()
except:
    NEWEST_VERSION = "UNKNOWN"

def time_str() -> str:
    return str(datetime.datetime.now())

s = socket.socket()
try:
    s.bind((config['general']['server_ip'], config['general']['server_port']))
except Exception as err:
    print("[Error] 绑定端口失败，可能的原因有：\n1. 端口已被占用\n2. 没有权限绑定该端口\n错误信息：\n" + str(err))
    exit()
s.listen(config['join']['max_connections'])
s.setblocking(False)

users = [{"body": None, "extra": None, "ip": None, "username": "root", "joined": True, "online": True, "admin": True}]
a = socket.socket()
a.connect(("127.0.0.1", config['general']['server_port']))
users[0]['body'], users[0]['ip'] = s.accept()
# 心跳包防止断连
if platform.system() == "Windows":
    users[0]['body'].setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
    users[0]['body'].ioctl(socket.SIO_KEEPALIVE_VALS, (1, 180 * 1000, 30 * 1000))
else:
    users[0]['body'].setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
    users[0]['body'].setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 180 * 60)
    users[0]['body'].setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)

with open("./log.txt", "a", encoding="utf-8") as file:
    file.write(json.dumps({'type': 'MISC.SERVER_START', 'time': time_str(), 'server_version': VERSION, 'config': config}) + "\n")
    file.write(json.dumps({'type': 'JOIN.LOG.CLIENT_REQUEST', 'time': time_str(), 'ip': users[0]['ip'], 'username': 'root', 'uid': 0}) + "\n")
    file.write(json.dumps({'type': 'JOIN.LOG.RESPONSE_DETAIL.ACCEPTED', 'time': time_str(), 'uid': 0, 'operator': -1}) + "\n")
    file.write(json.dumps({'type': 'MISC.ADMIN.LOG.ADD', 'time': time_str(), 'uid': 0}) + "\n")

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

EXIT_FLAG = False
log_queue = queue.Queue()
receive_queue = queue.Queue()
send_queue = queue.Queue()
history = []
all_history = []
online_count = 0

def thread_join():
    global online_count
    global log_queue
    global users
    global send_queue
    global history
    conntmp = None
    addresstmp = None
    while True:
        time.sleep(0.1)
        if EXIT_FLAG:
            exit()
            break
        
        conntmp, addresstmp = None, None
        try:
            conntmp, addresstmp = s.accept()
        except:
            continue
        
        time.sleep(3)
        data = ""
        while True:
            try:
                data += conntmp.recv(16384).decode('utf-8')
            except:
                break
        
        tagged = False
        for method in ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']:
            if method in data:
                try:
                    conntmp.send(bytes(WEBPAGE_CONTENT, encoding="utf-8"))
                    conntmp.close()
                except:
                    pass
                tagged = True
                log_queue.put(json.dumps({'type': 'JOIN.LOG.INCORRECT_PROTOCOL', 'time': time_str(), 'ip': addresstmp}))
                break
        if tagged:
            continue
        
        try:
            data = json.loads(data)
            if not isinstance(data, dict) or set(data.keys()) != {"type", "username"} or data['type'] != "JOIN.REQUEST" or not isinstance(data['username'], str) or not data['username']:
                raise
        except:
            log_queue.put(json.dumps({'type': 'JOIN.LOG.INCORRECT_PROTOCOL', 'time': time_str(), 'ip': addresstmp}))
            conntmp.close()
            continue
        
        uid = len(users)
        log_queue.put(json.dumps({'type': 'JOIN.LOG.CLIENT_REQUEST', 'time': time_str(), 'ip': addresstmp, 'username': data['username'], 'uid': uid}))
        users.append({"body": conntmp, "extra": None, "ip": addresstmp, "username": data['username'], "joined": False, "online": True, "admin": False})
        users[uid]['body'].send(bytes(json.dumps({'type': 'JOIN.RESPONSE.FETCHED'}) + "\n", encoding="utf-8"))
        
        if users[uid]['ip'][0] in config['ban']['ip']:
            users[uid]['body'].send(bytes(json.dumps({'type': 'JOIN.RESPONSE.REJECTED', 'operator': {'username': 'IP is banned', 'uid': -1}}) + "\n", encoding="utf-8"))
            log_queue.put(json.dumps({'type': 'JOIN.LOG.RESPONSE_DETAIL.REJECTED', 'time': time_str(), 'uid': uid, 'operator': -1}))
            users[uid]['online'] = False
            users[uid]['body'].close()
            continue
        
        if online_count == config['join']['max_connections']:
            users[uid]['body'].send(bytes(json.dumps({'type': 'JOIN.RESPONSE.REJECTED', 'operator': {'username': 'Room is full', 'uid': -2}}) + "\n", encoding="utf-8"))
            log_queue.put(json.dumps({'type': 'JOIN.LOG.RESPONSE_DETAIL.REJECTED', 'time': time_str(), 'uid': uid, 'operator': -2}))
            users[uid]['online'] = False
            users[uid]['body'].close()
            continue
        
        for user in users[:-1]:
            if user['online'] and users[uid]['username'] == user['username']:
                users[uid]['body'].send(bytes(json.dumps({'type': 'JOIN.RESPONSE.REJECTED', 'operator': {'username': 'Duplicate usernames', 'uid': -3}}) + "\n", encoding="utf-8"))
                log_queue.put(json.dumps({'type': 'JOIN.LOG.RESPONSE_DETAIL.REJECTED', 'time': time_str(), 'uid': uid, 'operator': -3}))
                users[uid]['online'] = False
                users[uid]['body'].close()
                break
        
        if users[uid]['online'] == False:
            continue
        
        for word in config['ban']['words']:
            if word in users[uid]['username']:
                users[uid]['body'].send(bytes(json.dumps({'type': 'JOIN.RESPONSE.REJECTED', 'operator': {'username': 'Username consists of banned words', 'uid': -4}}) + "\n", encoding="utf-8"))
                log_queue.put(json.dumps({'type': 'JOIN.LOG.RESPONSE_DETAIL.REJECTED', 'time': time_str(), 'uid': uid, 'operator': -4}))
                users[uid]['online'] = False
                users[uid]['body'].close()
                break
        
        if users[uid]['online'] == False:
            continue
        
        if platform.system() != "Windows":
            users[uid]['body'].setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
            users[uid]['body'].setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 180 * 60)
            users[uid]['body'].setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)
        else:
            users[uid]['body'].setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
            users[uid]['body'].ioctl(socket.SIO_KEEPALIVE_VALS, (1, 180 * 1000, 30 * 1000))
        
        if not config['join']['enter_check']:
            log_queue.put(json.dumps({'type': 'JOIN.LOG.RESPONSE_DETAIL.ACCEPTED', 'time': time_str(), 'uid': uid, 'operator': -1}))
            users[uid]['joined'] = True
            online_count += 1
            users_abstract = []
            for i in range(len(users)):
                users_abstract.append({"username": users[i]['username'], "joined": users[i]['joined'], "online": users[i]['online'], "admin": users[i]['admin']})
            users[uid]['body'].send(bytes(json.dumps({'type': 'JOIN.RESPONSE.ACCEPTED', 'server_version': VERSION, 'uid': uid, 'operator': {'username': 'Automatically accepted', 'uid': -1}, 'enter_hint': config['general']['enter_hint'], 'users': users_abstract, 'chat_history': history }) + "\n", encoding="utf-8"))
            for i in range(len(users)):
                if users[i]['joined'] and users[i]['online'] and i != uid:
                    send_queue.put(json.dumps({'to': i, 'content': {'type': 'MISC.JOIN_HINT', 'username': users[uid]['username'], 'uid': uid}}))
            continue
        
        for i in range(len(users)):
            if users[i]['admin']:
                send_queue.put(json.dumps({'to': i, 'content': {'type': 'JOIN.ENTER_CONFIRMATION_REQUEST', 'ip': users[uid]['ip'], 'username': users[uid]['username'], 'uid': uid}}))

def thread_send():
    global online_count
    global send_queue
    global log_queue
    global users
    while True:
        time.sleep(0.1)
        if EXIT_FLAG:
            exit()
            break
        while not send_queue.empty():
            message = json.loads(send_queue.get())
            try:
                users[message['to']]['body'].send(bytes(json.dumps(message['content']) + "\n", encoding="utf-8"))
            except:
                users[message['to']]['online'] = False
                online_count -= 1
                log_queue.put(json.dumps({'type': 'MISC.LEAVE_HINT.LOG', 'time': time_str(), 'uid': message['to']}))
                for i in range(len(users)):
                    if users[i]['joined'] and users[i]['online']:
                        send_queue.put(json.dumps({'to': i, 'content': {'type': 'MISC.LEAVE_HINT.ANNOUNCE', 'uid': message['to']}}))





INTRODUCTION_TEMPLATE = \
"""
欢迎使用 TouchFish 聊天室！当前版本：{}，最新版本：{}
如果想知道有什么命令，请输入 help。
具体的使用指南，参见 help <你想用的命令>。
详细的使用指南，见 wiki：
https://github.com/2044-space-elevator/TouchFish/wiki/How-to-use-chat
配置文件位于目录下的 ./config.json。
"""

class Server(cmd.Cmd):
    prompt = "TouchFish-Server@{}:{}> ".format(config['general']['server_ip'], config['general']['server_port'])
    intro = INTRODUCTION_TEMPLATE[1:].format(VERSION, NEWEST_VERSION)
    
    def __init__(self):
        cmd.Cmd.__init__(self)
    
    def do_cmd(self, arg):
        """
        使用方法 (~ 表示 cmd):
            ~ <cmd> 执行这个系统命令，并输出结果
        """
        if not arg.strip():
            print("参数错误。")
            return
        try:
            result = os.system(arg)
            if result != 0:
                print("命令执行失败！返回值: " + str(result))
        except Exception as err:
            print("命令执行失败！错误信息：", err)
    
    def do_user(self, arg):
        """
        显示聊天室内的用户
        """
        admin = []
        online = []
        pending = []
        offline = []
        
        for i in range(len(users)):
            if not users[i]['online']:
                offline.append(i)
                continue
            if not users[i]['joined']:
                pending.append(i)
                continue
            if not users[i]['admin']:
                online.append(i)
                continue
            admin.append(i)
        
        if admin:
            print("管理员：")
            print(" UID  IP                        用户名")                 
            for i in admin:
                print("{:>4}  {:<26}{}".format(i, "{}:{}".format(users[i]['ip'][0], users[i]['ip'][1]), users[i]['username']))
        if online:
            print("普通用户：")
            print(" UID  IP                        用户名")                 
            for i in online:
                print("{:>4}  {:<26}{}".format(i, "{}:{}".format(users[i]['ip'][0], users[i]['ip'][1]), users[i]['username']))
        if pending:
            print("等待加入用户：")
            print(" UID  IP                        用户名")                 
            for i in pending:
                print("{:>4}  {:<26}{}".format(i, "{}:{}".format(users[i]['ip'][0], users[i]['ip'][1]), users[i]['username']))
        if offline:
            print("已离线的用户：")
            print(" UID  IP                        用户名")                 
            for i in offline:
                print("{:>4}  {:<26}{}".format(i, "{}:{}".format(users[i]['ip'][0], users[i]['ip'][1]), users[i]['username']))
    
    def do_exit(self, arg):
        """
        退出当前程序
        """
        global log_queue
        global EXIT_FLAG
        log_queue.put(json.dumps({'type': 'MISC.SERVER_STOP', 'time': time_str()}))
        EXIT_FLAG = True
        exit()

server = Server()





def thread_check():
    global online_count
    global send_queue
    global log_queue
    global users
    timer = 10
    while True:
        time.sleep(1)
        if EXIT_FLAG:
            exit()
            break
        timer -= 1
        if timer:
            continue
        timer = 10
        down = []
        for i in range(len(users)):
            if users[i]['online']:
                try:
                    users[i]['body'].send(bytes("\n", encoding="utf-8"))
                except:
                    users[i]['online'] = False
                    down.append(i)
                    online_count -= 1
                    log_queue.put(json.dumps({'type': 'MISC.LEAVE_HINT.LOG', 'time': time_str(), 'uid': i}))
        for i in down:
            for j in range(len(users)):
                if users[j]['joined'] and users[j]['online']:
                    send_queue.put(json.dumps({'to': j, 'content': {'type': 'MISC.LEAVE_HINT.ANNOUNCE', 'uid': i}}))

def thread_log():
    global log_queue
    while True:
        time.sleep(1)
        if not log_queue.empty():
            with open("./log.txt", "a", encoding="utf-8") as file:
                while not log_queue.empty():
                    file.write(log_queue.get() + "\n")
        if EXIT_FLAG:
            exit()
            break

THREAD_CMD = threading.Thread(target=server.cmdloop)
# THREAD_RECEIVE = threading.Thread(target=thread_receive)
THREAD_SEND = threading.Thread(target=thread_send)
THREAD_JOIN = threading.Thread(target=thread_join)
# THREAD_FILE = threading.Thread(target=thread_file)
# THREAD_PROCESS = threading.Thread(target=thread_process)
THREAD_CHECK = threading.Thread(target=thread_check)
THREAD_LOG = threading.Thread(target=thread_log)

THREAD_CMD.start()
# THREAD_RECEIVE.start()
THREAD_SEND.start()
THREAD_JOIN.start()
# THREAD_FILE.start()
# THREAD_PROCESS.start()
THREAD_CHECK.start()
THREAD_LOG.start()

# Test Script
"""
import socket
import time
p = [None] * 20
def add(id, name):
    p[id] = socket.socket()
    p[id].connect(("127.0.0.1", 8080))
    p[id].send(bytes('{{"type": "JOIN.REQUEST", "username": "{}"}}\n'.format(name), encoding="utf-8"))
def get(id):
    print(p[id].recv(16384).decode("utf-8"))
def stop(id):
    p[id].close()
"""
