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

VERSION = "v4.0.0-alpha.3"

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

def enter():
    print("请输入消息，按 Ctrl + C 结束。")
    message = ""
    while True:
        try:
            message += input() + "\n"
        except EOFError:
            break
    return message

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

def do_cmd(self, arg):
    """
    使用方法 (~ 表示 cmd):
        ~ <cmd>                 执行某个系统命令，并输出结果
    """
    if not arg:
        print("命令执行失败！错误信息：命令不能为空。")
        return
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
    message = enter()
    if not message:
        print("操作失败：消息不能为空。")
        log_queue.put(json.dumps({'type': 'CHAT.LOG', 'time': time_str(), 'from': 0, 'content': message, 'to': -1, 'success': False}))
        return
    if len(message) > config['message']['max_length']:
        print("操作失败：消息太长。")
        log_queue.put(json.dumps({'type': 'CHAT.LOG', 'time': time_str(), 'from': 0, 'content': message, 'to': -1, 'success': False}))
        return
    for word in config['ban']['words']:
        if word in message and success:
            print("操作失败：消息中包含屏蔽词：" + word)
            log_queue.put(json.dumps({'type': 'CHAT.LOG', 'time': time_str(), 'from': 0, 'content': message, 'to': -1, 'success': False}))
            return
    log_queue.put(json.dumps({'type': 'CHAT.LOG', 'time': time_str(), 'from': 0, 'content': message, 'to': -1, 'success': True}))
    history.append({'time': time_str(), 'from': 0, 'content': message, 'to': -1})
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
    arg = arg.split(' ', 1)
    if len(arg) != 2:
        print("参数错误：应当给出恰好 2 个参数。")
        return
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
        log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE.LOG', 'time': time_str(), 'status': 'Online', 'uid': arg[1], 'operator': 0}))
        for i in range(len(users)):
            if users[i]['status'] in ["Online", "Admin"]:
                send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE.ANNOUNCE', 'status': 'Online', 'uid': arg[1], 'operator': 0}}))
        users[arg[1]]['status'] = "Online"
        users_abstract = []
        for i in range(len(users)):
            users_abstract.append({"username": users[i]['username'], "status": users[i]['status']})
        send_queue.put(json.dumps({'to': arg[1], 'content': {'type': 'SERVER.DATA', 'server_version': VERSION, 'uid': arg[1], 'config': config, 'users': users_abstract, 'chat_history': history}}))

    if arg[0] == "reject":
        users[arg[1]]['status'] = "Rejected"
        users[arg[1]]['body'].send(bytes(json.dumps({'type': 'GATE.REVIEW_RESULT', 'accepted': False, 'operator': {'username': 'root', 'uid': 0}}) + "\n", encoding="utf-8"))
        log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE.LOG', 'time': time_str(), 'status': 'Rejected', 'uid': arg[1], 'operator': 0}))
        for i in range(len(users)):
            if users[i]['status'] in ["Online", "Admin"]:
                send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE.ANNOUNCE', 'status': 'Rejected', 'uid': arg[1], 'operator': 0}}))
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
    if not arg:
        print("参数错误：应当给出恰好 1 个参数。")
        return
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
    log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE.LOG', 'time': time_str(), 'status': 'Kicked', 'uid': arg, 'operator': 0}))
    for i in range(len(users)):
        if users[i]['status'] in ["Online", "Admin"]:
            send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE.ANNOUNCE', 'status': 'Kicked', 'uid': arg, 'operator': 0}}))
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
    arg = arg.split(' ', 1)
    if len(arg) != 2:
        print("参数错误：应当给出恰好 2 个参数。")
        return
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
        log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE.LOG', 'time': time_str(), 'status': 'Admin', 'uid': arg[1], 'operator': 0}))
        for i in range(len(users)):
            if users[i]['status'] in ["Online", "Admin"]:
                send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE.ANNOUNCE', 'status': 'Admin', 'uid': arg[1], 'operator': 0}}))

    if arg[0] == 'remove':
        if arg[1] <= 0 or arg[1] >= len(users):
            print("UID 输入错误。")
            return
        if users[arg[1]]['status'] != "Admin":
            print("只能对状态为 Admin 的用户操作。")
            return
        users[arg[1]]['status'] = "Online"
        log_queue.put(json.dumps({'type': 'GATE.STATUS_CHANGE.LOG', 'time': time_str(), 'status': 'Online', 'uid': arg[1], 'operator': 0}))
        for i in range(len(users)):
            if users[i]['status'] in ["Online", "Admin"]:
                send_queue.put(json.dumps({'to': i, 'content': {'type': 'GATE.STATUS_CHANGE.ANNOUNCE', 'status': 'Online', 'uid': arg[1], 'operator': 0}}))
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
    if len(arg) != 1 and len(arg) != 3:
        print("参数错误：应当给出恰好 1 个或恰好 3 个参数。")
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
    