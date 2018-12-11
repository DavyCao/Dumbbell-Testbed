import socket
import subprocess

s = socket.socket()
s.bind(('0.0.0.0', 6001))
s.listen(100)
while True:
    c, addr = s.accept()
    print("Got connection from", addr)
    cmd = c.recv(1024).decode()
    print(cmd)

    if cmd == "Terminate!":
        c.close()
        s.close()
        break

    if "Start!" in cmd:
        res = subprocess.run("iperf3 -c 192.168.2.2 -t 10 -i 1 -R -p 5001", shell=True, stdout=subprocess.PIPE)

    print(res.stdout.decode())
    msg = res.stdout.decode().splitlines()[-3]
    c.sendall(msg.encode())
    c.close()