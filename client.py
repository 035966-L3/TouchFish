import socket
import tkinter as tk
import threading as thread

root = tk.Tk()
root.title("Connect to IP:")

CONNECT_IP = None
USER_NAME = None
USER_input = None
IP_input = None
PORT_input = None

def show():
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
        text_box.insert('end', rcv_data)
        text_box.see("end")
    #text_box.insert(tk.END, "114514")
    text_box.pack()
    tmp = tk.Label(rt, text="发送信息：")
    tmp.pack()
    msg_input = tk.Text(rt, width=50, height=3, font=('微软雅黑', 20, ""))
    def get_msg():
        tmpp = msg_input.get("1.0", "end")
        while tmpp[-1] == '\n':
            tmpp = tmpp[:-1]
        tmpp += '\n'
        s.send(bytes(f"{USER_NAME}: {tmpp}", encoding="utf-8"))    
    but = tk.Button(rt, text="发送", command=get_msg)
    msg_input.pack()
    but.pack()
    #fst()
    while 1:
        rt.update_idletasks()
        rt.update()
        receive_msg()

label = tk.Label(root, text="Connect to IP:")
IP_input = tk.Entry(root, width=20)
lb2 = tk.Label(root, text="Username: ")
USER_input = tk.Entry(root, width=20)
lb3 = tk.Label(root, text="Connect to port")
PORT_input = tk.Entry(root, width=20)

but = tk.Button(root, text="确定", command=show)
label.pack()
IP_input.pack()
lb2.pack()
USER_input.pack()
lb3.pack()
PORT_input.pack()
but.pack()
root.mainloop()



# s = socket.socket()

# ip = input("Connect to IP:")
# s.connect(ip, 5001))

# while 1:
#     send = input('Msg to server:')
#     if send == "exit":
#         break;
#     s.send(bytes(send, encoding="utf-8"))
#     rcv_data = s.recv(1024).decode("UTF-8")
#     print(f"Msg from server: {rcv_data}")
# s.close()