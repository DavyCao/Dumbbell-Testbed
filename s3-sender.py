import socket
import subprocess

s = socket.socket()
s.bind(('0.0.0.0', 6001))
s.listen(100)
id = -1
while True:
    c, addr = s.accept()
    print("Got connection from", addr)
    cmd = c.recv(1024).decode()
    print(cmd)

    if cmd == "Terminate!":
        subprocess.run("pkill iperf3", shell=True)
        c.close()
        s.close()
        break

    if "Start!" in cmd and id == -1:
        subprocess.run("iperf3 -s -p 5001 &", shell=True)
        id = 1
    c.close()