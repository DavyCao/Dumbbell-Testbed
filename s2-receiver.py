import socket
import subprocess
import datetime

d = datetime.datetime.now()
filename = "/tmp/experiment_logs/Receiver_" + "{:%y%m%d_%H%M%S}".format(d) + ".log"

s = socket.socket()
s.bind(('0.0.0.0', 6001))
s.listen(1000)

while True:
    f = open(filename, 'a+')
    c, addr = s.accept()
    print("Got connection from", addr, file=f)
    cmd = c.recv(1024).decode()
    print(cmd, file=f)

    if cmd == "cubic" or cmd == "bbr":
        print("Switching congestion control to: " + cmd, file=f)
        subprocess.run("sysctl -w net.ipv4.tcp_congestion_control=" + cmd, shell=True, stdout=subprocess.PIPE)
        c.close()
        continue

    elif cmd == "Terminate!":
        c.close()
        s.close()
        break

    elif "Start!" in cmd:
        # Check cc
        subprocess.run("sysctl -a | grep 'net.ipv4.tcp_congestion_control'", shell=True)

        res = subprocess.run("iperf3 -c 192.168.3.2 -t 30 -i 1 -R -p 5001", shell=True, stdout=subprocess.PIPE)
        print(res.stdout.decode(), file=f)
        msg = res.stdout.decode().splitlines()[-4] + "\n" + res.stdout.decode().splitlines()[-3] 
        c.sendall(msg.encode())

    c.close()
    f.close()