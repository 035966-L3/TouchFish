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
import re
import requests

VERSION = "v4.0.0-prealpha.24"

config = \
{
    "general": {"server_ip": "0.0.0.0", "server_port": 8080, "enter_hint": ""},
    "ban": {"ip": [], "words": []},
    "gate": {"enter_check": False, "max_connections": 256},
    "message": {"allow_private": True, "max_length": 16384},
    "file": {"allow_any": True, "allow_private": True, "max_size": 4294967296}
}

CONFIG_PATH = "config_server.json"

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
    print("检测到合法的配置文件，请确认参数。")
    print("未指定的参数将使用配置文件中给定的值。")
except:
    print("没有检测到合法的配置文件，请手动指定参数。")
    print("未指定的参数将使用列出的默认值。")
print(CONFIG_HINT)
print(CONFIG_LIST.format(config['general']['server_ip'], config['general']['server_port'], config['gate']['enter_check'], config['gate']['max_connections'], config['message']['allow_private'], config['message']['max_length'], config['file']['allow_any'], config['file']['allow_private'], config['file']['max_size'], config['general']['enter_hint'], config['ban']['ip'], config['ban']['words']))
if config['file']['allow_private'] and not config['file']['allow_any']:
    print("检测到 file.allow_any 被设置为 False 而 file.allow_private 被设置为 True。")
    print("这看起来不像是正常配置，请仔细检查。")
    print()
    print()
while True:
    try:
        command = input()
        if command == "done":
            break
        key, value = command.split(' ', 1)
        if not key in CONFIG_TYPE_CHECK_TABLE:
            print("该参数不存在。")
            raise
        if key == "general.server_ip" or key == "general.enter_hint":
            print("请注意，本参数修改时输入数据需要带引号并转义。")
            print("例如，将进入提示设为英文 Hi there! 并且末尾换行：")
            print(r'  general.enter_hint "Hi there!\n"')
            if not input("确定要继续吗？[y/N] ") in ['y', 'Y']:
                continue
        if key == "ban.ip" or key == "ban.words":
            print("请注意，本参数修改时 <value> 需要带引号并转义。")
            print("例如，将 fuck 和 shit 设置为屏蔽词：")
            print(r'  config set ban.words ["fuck", "shit"]')
            print("该操作将【清空】原有的屏蔽词列表（或 IP 黑名单），请谨慎操作！")
            if not input("确定要继续吗？[y/N] ") in ['y', 'Y']:
                continue
        if not eval("isinstance({}, {})".format(value, CONFIG_TYPE_CHECK_TABLE[key])):
            print("输入数据的类型与参数不匹配。")
            raise
        if CONFIG_TYPE_CHECK_TABLE[key] == "int" and int(value) <= 0 or CONFIG_TYPE_CHECK_TABLE[key] == "int" and int(value) >= 4294967297:
            print("输入的数值必须是不大于 4294967296 的正整数。")
            raise
        if CONFIG_TYPE_CHECK_TABLE[key] == "list":
            for item in eval(value):
                if not isinstance(item, str):
                    print("列表中的元素必须是 str（字符串）类型。")
                    raise
            if len(eval(value)) != len(set(eval(value))):
                print("列表中不能出现重复元素。")
                raise
        if key == "ban.words":
            for item in eval(value):
                if '\n' in item or '\r' in item or not item:
                    print("屏蔽词列表中不能出现空串和换行符。")
                    raise
        if key == "ban.ip":
            for item in eval(value):
                if not check_ip(item):
                    print("IP 黑名单中的元素 {} 不是有效的点分十进制格式 IPv4 地址。".format(item))
                    raise
        if key == "general.server_ip" and not check_ip(eval(value)):
            print("输入的服务器 IP 不是有效的点分十进制格式 IPv4 地址。")
            raise
        if key == "general.server_port" and eval(value) >= 65536:
            print("服务器端口号不能大于 65535。")
            raise
        if key == "file.allow_private" and eval(value) and not config['file']['allow_any']:
            print("请注意，仅将 file.allow_private 参数设置为 True 是无效的，")
            print("因为 file.allow_any 参数被设置为 False。")
            if not input("是否要同时将 file.allow_any 参数设置为 True？[Y/n] ") in ['n', 'N']:
                config['file']['allow_any'] = True
        if key == "file.allow_any" and config['file']['allow_private'] and not eval(value):
            print("请注意，当前 file.allow_private 参数被设置为 True，")
            print("它将在 file.allow_any 参数被设置为 False 后失效。")
            if not input("是否要同时将 file.allow_private 参数设置为 False？[Y/n] ") in ['n', 'N']:
                config['file']['allow_private'] = False
        first, second = key.split('.')
        config[first][second] = eval(value)
        print("操作成功。")
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        print("命令格式不正确，请重试。")
try:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f)
    print("参数已经成功保存到配置文件 {}，下次启动时将自动加载配置项。".format(CONFIG_PATH))
except:
    print("警告：无法将参数保存到配置文件 {}，请在聊天室启动后输入 config save 重试。".format(CONFIG_PATH))
print()

try:
    NEWEST_VERSION = requests.get("https://bopid.cn/chat/newest_version_chat.html", timeout=3).content.decode()
except:
    NEWEST_VERSION = "UNKNOWN"

def time_str():
    return str(datetime.datetime.now())

s = socket.socket()
try:
    s.bind((config['general']['server_ip'], config['general']['server_port']))
except Exception as err:
    print("绑定端口失败，可能的原因有：")
    print("1. 端口已被占用")
    print("2. 没有权限绑定该端口")
    print("错误信息：")
    print(str(err))
    exit()
s.listen(config['gate']['max_connections'])
s.setblocking(False)

users = [{"body": None, "extra": None, "buffer": "", "ip": (config['general']['server_ip'], config['general']['server_port']), "username": "root", "status": "Root"}]

with open("./log.txt", "a", encoding="utf-8") as file:
    file.write(json.dumps({'type': 'SERVER.START', 'time': time_str(), 'server_version': VERSION, 'config': config}) + "\n")

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

INTRODUCTION_TEMPLATE = \
"""
欢迎使用 TouchFish 聊天室！当前版本：{}，最新版本：{}
如果想知道有什么命令，请输入 help。
具体的使用指南，参见 help <您想用的命令>。
详细的使用指南，见 wiki：
https://github.com/2044-space-elevator/TouchFish/wiki/How-to-use-chat
用户列表中的 root 用户 (UID = 0) 代指本服务端程序自身，不计入连接数限制。
配置文件位于目录下的 ./{}。

"""

EXIT_FLAG = False
log_queue = queue.Queue()
receive_queue = queue.Queue()
send_queue = queue.Queue()
history = []
all_history = []
online_count = 0





class Server(cmd.Cmd):
    prompt = "TouchFish-Server@{}:{}> ".format(config['general']['server_ip'], config['general']['server_port'])
    intro = INTRODUCTION_TEMPLATE[1:].format(VERSION, NEWEST_VERSION, CONFIG_PATH)
    
    def __init__(self):
        cmd.Cmd.__init__(self)
    
    def do_cmd(self, arg):
        """
        使用方法 (~ 表示 cmd):
            ~ <cmd>                 执行某个系统命令，并输出结果
        """
        try:
            result = os.system(arg)
            if result != 0:
                print("命令执行失败！返回值: " + str(result))
            if result == 0:
                print("操作成功。")
        except Exception as err:
            print("命令执行失败！错误信息：", err)
    
    def do_user(self, arg):
        """
        显示聊天室内的用户
        """
        print(" UID  IP                        状态      用户名") 
        for i in range(len(users)):
            print("{:>4}  {:<26}{:<10}{}".format(i, "{}:{}".format(users[i]['ip'][0], users[i]['ip'][1]), users[i]['status'], users[i]['username']))
    
    def do_broadcast(self, arg):
        """
        广播消息
        """
        print("请输入消息，按 Ctrl + C 结束。")
        message = ""
        while True:
            try:
                message += input() + "\n"
            except EOFError:
                break
        log_queue.put(json.dumps({'type': 'CHAT.LOG', 'time': time_str(), 'uid': 0, 'content': message, 'to': -1, 'success': True}))
        for i in range(len(users)):
            if users[i]['status'] in ["Online", "Admin"]:
                send_queue.put(json.dumps({'to': i, 'content': {'type': 'CHAT.RECEIVE', 'from': 0, 'content': message, 'to': -1}}))
        print("操作成功。")
    
    def do_doorman(self, arg):
        """
        使用方法 (~ 表示 doorman):
            ~ accept <uid>          通过某个用户的加入申请
            ~ reject <uid>          拒绝某个用户的加入申请
        """
        global log_queue
        global send_queue
        global online_count
        arg = arg.split()
        try:
            arg[1] = int(arg[1])
        except:
            print("参数错误：UID 必须是整数。")
            return
        if not arg[0] in ['accept', 'reject']:
            print("参数错误：第一个参数必须是 accept 和 reject 中的某一项。")
            return
        if arg[1] <= -1 or arg[1] >= len(users):
            print("UID 输入错误。")
            return
        if users[arg[1]]['status'] != "Pending":
            print("只能对状态为 Pending 的用户操作。")
            if users[arg[1]]['status'] in ["Online", "Admin"] and arg[0] == "reject":
                print("您似乎想要踢出该用户，请使用以下命令：kick {}".format(arg))
            return
        
        if arg[0] == "accept":
            send_queue.put(json.dumps({'to': arg[1], 'content': {'type': 'GATE.REVIEW_RESULT', 'accepted': True, 'operator': {'username': 'root', 'uid': 0}}}))
            log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE_HINT.LOG', 'time': time_str(), 'status': 'Online', 'uid': arg[1], 'operator': 0}))
            for i in range(len(users)):
                if users[i]['status'] in ["Online", "Admin"]:
                    send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE_HINT.ANNOUNCE', 'status': 'Online', 'uid': arg[1], 'operator': 0}}))
            users[arg[1]]['status'] = "Online"
            users_abstract = []
            for i in range(len(users)):
                users_abstract.append({"username": users[i]['username'], "status": users[i]['status']})
            send_queue.put(json.dumps({'to': arg[1], 'content': {'type': 'SERVER.DATA', 'server_version': VERSION, 'uid': arg[1], 'config': config, 'users': users_abstract, 'chat_history': history}}))
        
        if arg[0] == "reject":
            users[arg[1]]['status'] = "Rejected"
            users[arg[1]]['body'].send(bytes(json.dumps({'type': 'GATE.REVIEW_RESULT', 'accepted': False, 'operator': {'username': 'root', 'uid': 0}}) + "\n", encoding="utf-8"))
            log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE_HINT.LOG', 'time': time_str(), 'status': 'Rejected', 'uid': arg[1], 'operator': 0}))
            for i in range(len(users)):
                if users[i]['status'] in ["Online", "Admin"]:
                    send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE_HINT.ANNOUNCE', 'status': 'Rejected', 'uid': arg[1], 'operator': 0}}))
            users[arg[1]]['body'].close()
            online_count -= 1
            
        print("操作成功。")
    
    def do_kick(self, arg):
        """
        使用方法 (~ 表示 kick):
            ~ <uid>                 踢出某个用户
        """
        global log_queue
        global send_queue
        global online_count
        try:
            arg = int(arg)
        except:
            print("参数错误：UID 必须是整数。")
            return
        if arg <= -1 or arg >= len(users):
            print("UID 输入错误。")
            return
        if not users[arg]['status'] in ["Online", "Admin"]:
            print("只能对状态为 Online 或 Admin 的用户操作。")
            if users[arg]['status'] == "Pending":
                print("您似乎想要拒绝该用户的加入申请，请使用以下命令：doorman reject {}".format(arg))
            return
        log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE_HINT.LOG', 'time': time_str(), 'status': 'Kicked', 'uid': arg, 'operator': 0}))
        for i in range(len(users)):
            if users[i]['status'] in ["Online", "Admin"]:
                send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE_HINT.ANNOUNCE', 'status': 'Kicked', 'uid': arg, 'operator': 0}}))
        users[arg]['status'] = "Kicked"
        online_count -= 1
        print("操作成功。")
    
    def do_admin(self, arg):
        """
        使用方法 (~ 表示 admin):
            ~ add <uid>             添加管理员
            ~ remove <uid>          撤销管理员
        """
        global log_queue
        global send_queue
        arg = arg.split()
        if not arg[0] in ['add', 'remove']:
            print("参数错误：第一个参数必须是 add 或 remove。")
            return
        try:
            arg[1] = int(arg[1])
        except:
            print("参数错误：UID 必须是整数。")
            return
        
        if arg[0] == 'add':
            if arg[1] <= 0 or arg[1] >= len(users):
                print("UID 输入错误。")
                return
            if users[arg[1]]['status'] != "Online":
                print("只能对状态为 Online 的用户操作。")
                return
            users[arg[1]]['status'] = "Admin"
            log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE_HINT.LOG', 'time': time_str(), 'status': 'Admin', 'uid': arg[1], 'operator': 0}))
            for i in range(len(users)):
                if users[i]['status'] in ["Online", "Admin"]:
                    send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE_HINT.ANNOUNCE', 'status': 'Admin', 'uid': arg[1], 'operator': 0}}))
        
        if arg[0] == 'remove':
            if arg[1] <= 0 or arg[1] >= len(users):
                print("UID 输入错误。")
                return
            if users[arg[1]]['status'] != "Admin":
                print("只能对状态为 Admin 的用户操作。")
                return
            users[arg[1]]['status'] = "Online"
            log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE_HINT.LOG', 'time': time_str(), 'status': 'Online', 'uid': arg[1], 'operator': 0}))
            for i in range(len(users)):
                if users[i]['status'] in ["Online", "Admin"]:
                    send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE_HINT.ANNOUNCE', 'status': 'Online', 'uid': arg[1], 'operator': 0}}))
        print("操作成功。")
    
    def do_config(self, arg):
        """
        使用方法 (~ 表示 config):
            ~ show                  列出参数列表
            ~ set <name> <value>    将参数 <name> 的值改为 <value>
            ~ save                  将参数保存到配置文件
        """
        global log_queue
        global send_queue
        global config
        arg = arg.split(' ', 2)
        if not arg:
            print("参数错误：参数不能为空。")
            return
        if not arg[0] in ['show', 'set', 'save']:
            print("参数错误：第一个参数必须是 show、set、save 中的某一项。")
            return
        
        if arg[0] == 'show':
            print(CONFIG_LIST.format(config['general']['server_ip'], config['general']['server_port'], config['gate']['enter_check'], config['gate']['max_connections'], config['message']['allow_private'], config['message']['max_length'], config['file']['allow_any'], config['file']['allow_private'], config['file']['max_size'], config['general']['enter_hint'], config['ban']['ip'], config['ban']['words']))
            return
        
        if arg[0] == 'save':
            try:
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f)
                print("参数已经成功保存到配置文件 {}，下次启动时将自动加载配置项。".format(CONFIG_PATH))
                log_queue.put(json.dumps({'type': 'SERVER.CONFIG.SAVE', 'time': time_str()}))
            except:
                print("无法将参数保存到配置文件 {}，请稍后重试。".format(CONFIG_PATH))
            return
        
        if arg[0] == 'set':
            if not arg[1] in CONFIG_TYPE_CHECK_TABLE:
                print("该参数不存在。")
                return
            if arg[1] == "general.server_ip" or arg[1] == "general.server_port" or arg[1] == "gate.max_connections":
                print("不允许在命令行内修改该参数，请退出聊天室后重新打开以修改。")
                return
            if arg[1] == "general.enter_hint":
                print("请注意，本参数修改时 <value> 需要带引号并转义。")
                print("例如，将进入提示设为英文 Hi there! 并且末尾换行：")
                print(r'  config set general.enter_hint "Hi there!\n"')
                if not input("确定要继续吗？[y/N] ") in ['y', 'Y']:
                    return
            if arg[1] == "ban.ip" or arg[1] == "ban.words":
                print("请注意，本参数修改时 <value> 需要带引号并转义。")
                print("例如，将 fuck 和 shit 设置为屏蔽词：")
                print(r'  config set ban.words ["fuck", "shit"]')
                print("该操作将【清空】原有的屏蔽词列表（或 IP 黑名单），请谨慎操作！")
                if not input("确定要继续吗？[y/N] ") in ['y', 'Y']:
                    return
            
            try:
                if not eval("isinstance({}, {})".format(arg[2], CONFIG_TYPE_CHECK_TABLE[arg[1]])):
                    print("输入数据的类型与参数不匹配。")
                    raise
                if CONFIG_TYPE_CHECK_TABLE[arg[1]] == "int" and int(arg[2]) <= 0 or CONFIG_TYPE_CHECK_TABLE[arg[1]] == "int" and int(arg[2]) >= 4294967297:
                    print("输入的数值必须是不大于 4294967296 的正整数。")
                    raise
                if CONFIG_TYPE_CHECK_TABLE[arg[1]] == "list":
                    for item in eval(arg[2]):
                        if not isinstance(item, str):
                            print("列表中的元素必须是 str（字符串）类型。")
                            raise
                    if len(eval(arg[2])) != len(set(eval(arg[2]))):
                        print("列表中不能出现重复元素。")
                        raise
                if arg[1] == "ban.words":
                    for item in eval(arg[2]):
                        if '\n' in item or '\r' in item or not item:
                            print("屏蔽词列表中不能出现空串和换行符。")
                            raise
                if arg[1] == "ban.ip":
                    for item in eval(arg[2]):
                        if not check_ip(item):
                            print("IP 黑名单中的元素 {} 不是有效的点分十进制格式 IPv4 地址。".format(item))
                            raise
                if arg[1] == "file.allow_private" and eval(arg[2]) and not config['file']['allow_any']:
                    print("请注意，仅将 file.allow_private 参数设置为 True 是无效的，")
                    print("因为 file.allow_any 参数被设置为 False。")
                    if not input("是否要同时将 file.allow_any 参数设置为 True？[Y/n] ") in ['n', 'N']:
                        config['file']['allow_any'] = True
                        log_queue.put(json.dumps({'type': 'SERVER.CONFIG.LOG', 'time': time_str(), 'key': 'file.allow_any', 'value': True, 'operator': 0}))
                        for i in range(len(users)):
                            if users[i]['status'] in ["Online", "Admin"]:
                                send_queue.put(json.dumps({'to': i, 'content': {'type': 'SERVER.CONFIG.CHANGE', 'key': 'file.allow_any', 'value': True, 'operator': 0}}))
                if arg[1] == "file.allow_any" and config['file']['allow_private'] and not eval(arg[2]):
                    print("请注意，当前 file.allow_private 参数被设置为 True，")
                    print("它将在 file.allow_any 参数被设置为 False 后失效。")
                    if not input("是否要同时将 file.allow_private 参数设置为 False？[Y/n] ") in ['n', 'N']:
                        config['file']['allow_private'] = False
                        log_queue.put(json.dumps({'type': 'SERVER.CONFIG.LOG', 'time': time_str(), 'key': 'file.allow_private', 'value': False, 'operator': 0}))
                        for i in range(len(users)):
                            if users[i]['status'] in ["Online", "Admin"]:
                                send_queue.put(json.dumps({'to': i, 'content': {'type': 'SERVER.CONFIG.CHANGE', 'key': 'file.allow_private', 'value': False, 'operator': 0}}))
                
                first, second = arg[1].split('.')
                config[first][second] = eval(arg[2])
                log_queue.put(json.dumps({'type': 'SERVER.CONFIG.LOG', 'time': time_str(), 'key': first + '.' + second, 'value': eval(arg[2]), 'operator': 0}))
                for i in range(len(users)):
                    if users[i]['status'] in ["Online", "Admin"]:
                        send_queue.put(json.dumps({'to': i, 'content': {'type': 'SERVER.CONFIG.CHANGE', 'key': first + '.' + second, 'value': eval(arg[2]), 'operator': 0}}))
                print("操作成功。")
            except:
                print("命令格式不正确，请重试。")
            return
    
    def do_ban(self, arg):
        """
        使用方法 (~ 表示 ban):
            ~ ip add <ip>           封禁 IP（段）
            ~ ip remove <ip>        解除封禁 IP（段）
            ~ words add <word>      屏蔽某个词语
            ~ words remove <word>   解除屏蔽某个词语
        """
        global log_queue
        global send_queue
        global config
        arg = arg.split(' ', 2)
        if len(arg) != 3:
            print("参数错误：应当给出恰好 3 个参数。")
            return
        if not arg[0] in ['ip', 'words']:
            print("参数错误：第一个参数必须是 ip 和 words 中的某一项。")
            return
        if not arg[1] in ['add', 'remove']:
            print("参数错误：第二个参数必须是 add 和 remove 中的某一项。")
            return

        if arg[0] == 'ip':
            ips = check_ip_segment(arg[2])
            if ips == []:
                print("输入数据不是合法的点分十进制格式 IPv4 地址或 IPv4 段。")
                return
            if ips == [""]:
                print("出于性能、安全性和实际使用环境考虑，IPv4 段的 CIDR 不得小于 24。")
                return
            if arg[1] == 'add':
                ips = [item for item in ips if item not in config['ban']['ip']]
                config['ban']['ip'] += ips
                log_queue.put(json.dumps({'type': 'SERVER.CONFIG.LOG', 'time': time_str(), 'key': 'ban.ip', 'value': config['ban']['ip'], 'operator': 0}))
                for i in range(len(users)):
                    if users[i]['status'] in ["Online", "Admin"]:
                        send_queue.put(json.dumps({'to': i, 'content': {'type': 'SERVER.CONFIG.CHANGE', 'key': 'ban.ip', 'value': config['ban']['ip'], 'operator': 0}}))
                print("操作成功，共计封禁了 {} 个 IP 地址。".format(len(ips)))
            if arg[1] == 'remove':
                ips = [item for item in ips if item in config['ban']['ip']]
                config['ban']['ip'] = [item for item in config['ban']['ip'] if not item in ips]
                log_queue.put(json.dumps({'type': 'SERVER.CONFIG.LOG', 'time': time_str(), 'key': 'ban.ip', 'value': config['ban']['ip'], 'operator': 0}))
                for i in range(len(users)):
                    if users[i]['status'] in ["Online", "Admin"]:
                        send_queue.put(json.dumps({'to': i, 'content': {'type': 'SERVER.CONFIG.CHANGE', 'key': 'ban.ip', 'value': config['ban']['ip'], 'operator': 0}}))
                print("操作成功，共计解除封禁了 {} 个 IP 地址。".format(len(ips)))
        if arg[0] == 'words':
            if '\n' in item or '\r' in item or not item:
                print("屏蔽词不能为空串，且不能包含换行符。")
                return
            if ' ' in arg[2]:
                print("请注意，您输入的屏蔽词包含空格。")
                print("系统读取到的屏蔽词为（不包含开头的 ^ 符号和结尾的 $ 符号）：")
                print("^", arg[2], "$", sep="")
                if not input("确定要继续吗？[y/N] ") in ['y', 'Y']:
                    return
            if arg[1] == 'add':
                if arg[2] in config['ban']['words']:
                    print("该屏蔽词已经在列表中出现了。")
                    return
                config['ban']['words'].append(arg[2])
                log_queue.put(json.dumps({'type': 'SERVER.CONFIG.LOG', 'time': time_str(), 'key': 'ban.words', 'value': config['ban']['words'], 'operator': 0}))
                for i in range(len(users)):
                    if users[i]['status'] in ["Online", "Admin"]:
                        send_queue.put(json.dumps({'to': i, 'content': {'type': 'SERVER.CONFIG.CHANGE', 'key': 'ban.words', 'value': config['ban']['words'], 'operator': 0}}))
                print("操作成功。")
            if arg[1] == 'remove':
                if not arg[2] in config['ban']['words']:
                    print("该屏蔽词不在列表中。")
                    return
                config['ban']['words'].remove(arg[2])
                log_queue.put(json.dumps({'type': 'SERVER.CONFIG.LOG', 'time': time_str(), 'key': 'ban.words', 'value': config['ban']['words'], 'operator': 0}))
                for i in range(len(users)):
                    if users[i]['status'] in ["Online", "Admin"]:
                        send_queue.put(json.dumps({'to': i, 'content': {'type': 'SERVER.CONFIG.CHANGE', 'key': 'ban.words', 'value': config['ban']['words'], 'operator': 0}}))
                print("操作成功。")
    
    def do_exit(self, arg):
        """
        退出当前程序
        """
        global log_queue
        global EXIT_FLAG
        log_queue.put(json.dumps({'type': 'SERVER.STOP', 'time': time_str()}))
        EXIT_FLAG = True
        exit()





def thread_gate():
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
            conntmp.setblocking(False)
            conntmp.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            conntmp.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
        except:
            continue
        
        time.sleep(2)
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
                log_queue.put(json.dumps({'type': 'GATE.INCORRECT_PROTOCOL', 'time': time_str(), 'ip': addresstmp}))
                break
        if tagged:
            continue
        
        try:
            data = json.loads(data)
            if not isinstance(data, dict) or set(data.keys()) != {"type", "username"} or data['type'] != "GATE.REQUEST" or not isinstance(data['username'], str) or not data['username']:
                raise
        except:
            log_queue.put(json.dumps({'type': 'GATE.INCORRECT_PROTOCOL', 'time': time_str(), 'ip': addresstmp}))
            conntmp.close()
            continue
        
        uid = len(users)
        users.append({"body": conntmp, "extra": None, "buffer": "", "ip": addresstmp, "username": data['username'], "status": "Pending"})
        result = "Accepted"
        if config['gate']['enter_check']:
            result = "Pending review"
        if users[uid]['ip'][0] in config['ban']['ip']:
            result = "IP is banned"
        if online_count == config['gate']['max_connections']:
            result = "Room is full"
        for user in users[:-1]:
            if user['status'] in ["Online", "Admin", "Root"] and users[uid]['username'] == user['username']:
                result = "Duplicate usernames"
        for word in config['ban']['words']:
            if word in users[uid]['username']:
                result = "Username consists of banned words"
        
        users[uid]['body'].send(bytes(json.dumps({'type': 'GATE.RESPONSE', 'result': result}) + "\n", encoding="utf-8"))
        log_queue.put(json.dumps({'type': 'GATE.CLIENT_REQUEST.LOG', 'time': time_str(), 'ip': users[uid]['ip'], 'username': users[uid]['username'], 'uid': uid, 'result': result}))
        for i in range(len(users)):
            if users[i]['status'] in ["Online", "Admin"]:
                send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.CLIENT_REQUEST.ANNOUNCE', 'username': users[uid]['username'], 'uid': uid, 'result': result}}))
        
        if not result in ["Accepted", "Pending review"]:
            users[uid]['status'] = "Rejected"
            users[uid]['body'].close()
            continue
        if platform.system() != "Windows":
            users[uid]['body'].setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
            users[uid]['body'].setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 180 * 60)
            users[uid]['body'].setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)
        if platform.system() == "Windows":
            users[uid]['body'].setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
            users[uid]['body'].ioctl(socket.SIO_KEEPALIVE_VALS, (1, 180 * 1000, 30 * 1000))
        online_count += 1
        
        if result == "Accepted":
            users[uid]['status'] = "Online"
            users_abstract = []
            for i in range(len(users)):
                users_abstract.append({"username": users[i]['username'], "status": users[i]['status']})
            users[uid]['body'].send(bytes(json.dumps({'type': 'SERVER.DATA', 'server_version': VERSION, 'uid': uid, 'config': config, 'users': users_abstract, 'chat_history': history}) + "\n", encoding="utf-8"))

def thread_receive():
    global receive_queue
    global users
    while True:
        time.sleep(0.1)
        if EXIT_FLAG:
            exit()
            break
        for i in range(len(users)):
            if users[i]['status'] in ["Online", "Admin"]:
                data = ""
                while True:
                    try:
                        users[i]['body'].setblocking(False)
                        data += users[i]['body'].recv(16384).decode('utf-8')
                    except:
                        break
                users[i]['buffer'] += data
                while '\n' in users[i]['buffer']:
                    try:
                        message, users[i]['buffer'] = users[i]['buffer'].split('\n', 1)
                    except:
                        message, users[i]['buffer'] = users[i]['buffer'], ""
                    try:
                        message = json.loads(message)
                    except:
                        continue
                    receive_queue.put(json.dumps({'from': i, 'content': message}))

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
            if not users[message['to']]['status'] in ["Online", "Admin"]:
                continue
            try:
                users[message['to']]['body'].send(bytes(json.dumps(message['content']) + "\n", encoding="utf-8"))
            except:
                users[message['to']]['status'] = "Offline"
                online_count -= 1
                log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE_HINT.LOG', 'time': time_str(), 'status': 'Offline', 'uid': message['to'], 'operator': 0}))
                for i in range(len(users)):
                    if users[i]['status'] in ["Online", "Admin"]:
                        send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE_HINT.ANNOUNCE', 'status': 'Offline', 'uid': message['to'], 'operator': 0}}))

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
        timer = 5
        down = []
        for i in range(len(users)):
            if users[i]['status'] in ["Online", "Admin"]:
                try:
                    users[i]['body'].send(bytes("\n", encoding="utf-8"))
                except:
                    users[i]['status'] = "Offline"
                    down.append(i)
                    online_count -= 1
                    log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE_HINT.LOG', 'time': time_str(), 'status': 'Offline', 'uid': i, 'operator': 0}))
        for i in down:
            for j in range(len(users)):
                if users[j]['status'] in ["Online", "Admin"]:
                    send_queue.put(json.dumps({'to': j, 'content': {'type': 'GATE.STATUS_CHANGE_HINT.ANNOUNCE', 'status': 'Offline', 'uid': i, 'operator': 0}}))





server = Server()

THREAD_CMD = threading.Thread(target=server.cmdloop)
THREAD_GATE = threading.Thread(target=thread_gate)
# THREAD_PROCESS = threading.Thread(target=thread_process)
# THREAD_FILE = threading.Thread(target=thread_file)
THREAD_RECEIVE = threading.Thread(target=thread_receive)
THREAD_SEND = threading.Thread(target=thread_send)
THREAD_LOG = threading.Thread(target=thread_log)
THREAD_CHECK = threading.Thread(target=thread_check)

THREAD_CMD.start()
THREAD_GATE.start()
# THREAD_PROCESS.start()
# THREAD_FILE.start()
THREAD_RECEIVE.start()
THREAD_SEND.start()
THREAD_LOG.start()
THREAD_CHECK.start()

