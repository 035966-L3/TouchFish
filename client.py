import keyboard
import socket
import tkinter as tk
import winsound
import threading as thread
from sys import exit


CONNECT_IP = None
USER_NAME = None
USER_input = None
IP_input = None
PORT_input = None
exit_flg = 0
BELL = False
text_box = None
FONT_FAMILY = ("微软雅黑", 20, "")
exit_flg_2 = False

def setting():
    global exit_flg_2
    exit_flg_2 = False
    set_tk = tk.Toplevel()
    set_tk.title("设置")
    font_label = tk.Label(set_tk, text='字体名称')
    font_label.pack()
    font_entry = tk.Entry(set_tk) 
    font_entry.insert(0, FONT_FAMILY[0])
    font_entry.pack()
    
    font_size_label = tk.Label(set_tk, text="字号")
    font_size_label.pack()
    font_size_entry = tk.Entry(set_tk)
    font_size_entry.insert(0, FONT_FAMILY[1])
    font_size_entry.pack()

    ini_val = tk.BooleanVar(value=BELL) 
    bell_on_button = tk.Checkbutton(set_tk, text="是否开启语音提示（仅 Windows 支持）", variable=ini_val, onvalue=True, offvalue=False)
    bell_on_button.pack()

    def confirm_f():
        global exit_flg_2 
        global BELL
        global FONT_FAMILY
        try:
            fsize = int(font_size_entry.get())
            fname = font_entry.get()
            FONT_FAMILY = (fname, fsize, "")
            text_box.configure(font=FONT_FAMILY)
            BELL = ini_val.get()
        except:
            pass

        exit_flg_2 = True

    confirm = tk.Button(set_tk, text="确定", command=confirm_f)
    confirm.pack()

    def close_window():
        global exit_flg_2
        exit_flg_2 = True
    set_tk.protocol('WM_DELETE_WINDOW', close_window)

    while True:
        set_tk.update()
        set_tk.update_idletasks()
        if exit_flg_2:
            set_tk.destroy()
            return


root = tk.Tk()
root.title("Connect to IP:")
    

def show():
    global text_box
    s = socket.socket()
    USER_NAME = USER_input.get()
    CONNECT_IP = IP_input.get()
    CONNECT_PORT = PORT_input.get()
    root.destroy()
    s.connect((CONNECT_IP, eval(CONNECT_PORT)))
    rt = tk.Tk()
    rt.title(f"SERVER: {CONNECT_IP}")
    screen_width = rt.winfo_screenwidth()
    screen_height = rt.winfo_screenheight()
    rt.geometry(f"{screen_width}x{screen_height}")
    text_box = tk.Text(rt, width=screen_width, height=12, font=("微软雅黑", 20, ""))
    vsb = tk.Scrollbar(orient="vertical", command=text_box.yview)
    text_box.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    s.setblocking(0)
    def receive_msg():
        rcv_data = None
        try:
            rcv_data = s.recv(1024).decode("utf-8")
        except:
            return
        if (USER_NAME + ":" not in rcv_data) and rcv_data and BELL:
            winsound.Beep(1000,440)
        text_box.insert('end', rcv_data)
        text_box.see("end")

    text_box.pack()
    tmp = tk.Label(rt, text="发送信息：")
    tmp.pack()
    msg_input = tk.Text(rt, width=50, height=3, font=('微软雅黑', 20, ""))
    def send_msg():
        tmpp = msg_input.get("1.0", "end")
        if len(tmpp) == 0:
            return
        try:
            while tmpp[-1] == '\n' or tmpp[-1] == ' ':
                tmpp = tmpp[:-1]
        except:
            pass
        if len(tmpp) == 0:
            return
        tmpp += '\n'
        s.send(bytes(f"{USER_NAME}: {tmpp}", encoding="utf-8"))    
        msg_input.delete('1.0', 'end')

    but = tk.Button(rt, text="发送", command=send_msg)
    msg_input.pack()
    but.pack()
    but_set = tk.Button(rt, text="设置", command=setting)
    but_set.pack()

    def close_window():
        global exit_flg
        exit_flg = 1

    rt.protocol('WM_DELETE_WINDOW', close_window)
    while 1:
        if exit_flg:
            rt.destroy()
            exit()
            break
        rt.update_idletasks()
        rt.update()
        receive_msg()
        if keyboard.is_pressed('ctrl') and keyboard.is_pressed('1'):
            send_msg()

label = tk.Label(root, text="Connect to IP:")
IP_input = tk.Entry(root, width=20)
lb2 = tk.Label(root, text="Username: ")
USER_input = tk.Entry(root, width=20)
lb3 = tk.Label(root, text="Connect to port")
PORT_input = tk.Entry(root, width=20)

but = tk.Button(root, text="确定", command=show)

hint = tk.Label(root, text="提示：同时按下 Ctrl+1 可以发送信息")
set_hint2 = tk.Label(root, text="打开设置时，主窗口将暂停进程")

label.pack()
IP_input.pack()
lb2.pack()
USER_input.pack()
lb3.pack()
PORT_input.pack()
but.pack()
hint.pack()
set_hint2.pack()
root.mainloop()