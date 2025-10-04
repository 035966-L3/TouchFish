# now just test

import socket
import time
from sys import exit
import threading
import json
import cmd
import os

IP = input("Connect to IP:")
PORT = input("Connect to PORT:")
ADMIN_NAME = input("Username:")

try:
    PORT = int(PORT)
except:
    print("输入错误。")
    exit()

s = socket.socket()
s.connect((IP, PORT))
s.setblocking(False)

CONNECT_TIME = time.time()
while True:
    if time.time() - CONNECT_TIME > 40:
        print("服务器连接失败")
        exit()
    
    try:
        msg_str = s.recv(1024).decode("utf-8")
    except:
        continue
    msg = json.loads(msg_str)
    if msg["type"] == "test":
        print("连接成功！")
        break

s.send(bytes(json.dumps({"type" : "username", "message" : ADMIN_NAME}), encoding="utf-8"))

propt = f"{IP}:{PORT} (admin)> "
EXIT_FLG = False

def send_msg(typ : str, arg : str):
    try:
        s.send(bytes(json.dumps({"type" : typ, "message" : arg}), encoding="utf-8"))
    except:
        print("发送失败！\n" + propt, end="")

def receive_ret():
    while True:
        if EXIT_FLG:
            exit()
            break
        try:
            msg_str = s.recv(1024).decode("utf-8")
        except:
            continue
        msg_str = msg_str.split('}')
        for msg_str_sin in msg_str:
            msg_str_sin += '}'
            try:
                msg = json.loads(msg_str_sin)
            except:
                continue
            if msg["type"] == "result":
                if msg["message"]:
                    print('\n' + msg["message"] + propt, end="")

class Admin(cmd.Cmd):
    prompt = propt
    intro = "懒得写了，去看 server"

    def __init__(self):
        cmd.Cmd.__init__(self)

    def do_broadcast(self, arg):
        send_msg("broadcast", arg)
    
    def do_ban(self, arg):
        send_msg("ban", arg)
    
    def do_enable(self, arg):
        send_msg("enable", arg)
    
    def do_set(self, arg):
        send_msg("set", arg)
    
    def do_exit(self, arg):
        global EXIT_FLG
        EXIT_FLG = True
        exit()
    
    def do_accept(self, arg):
        send_msg("accept", arg)
    
    def do_reject(self, arg):
        send_msg("reject", arg)
    
    def do_search(self, arg):
        send_msg("search", arg)
    
    def do_req(self, arg):
        send_msg("req", arg)
    
    def do_flush(self, arg):
        send_msg("flush", "")

    def do_cmd(self, arg):
        """
        使用方法 (~ 表示 cmd):
            ~ <cmd> 执行这个系统命令，并输出结果
        """
        if not arg.strip():
            print("[ERROR] 参数错误")
            return
        try:
            result = os.system(arg)
            if result != 0:
                print("[ERROR] Command failed! Return code: " + str(result))
        except Exception as err:
            print("命令执行失败！错误信息:", err)

tr = threading.Thread(target=receive_ret)
tr.start()
admin = Admin()
tr2 = threading.Thread(target=admin.cmdloop)
tr2.start()
