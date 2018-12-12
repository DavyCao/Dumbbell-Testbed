import socket
import subprocess

s = socket.socket()
s.bind(('0.0.0.0', 6001))
s.listen(1000)
id = -1
while True:
    c, addr = s.accept()
    print("Got connection from", addr)
    cmd = c.recv(1024).decode()
    print(cmd)

    if cmd == "cubic" or cmd == "bbr":
        print("Switching congestion control to: " + cmd)
        subprocess.run("sysctl -w net.ipv4.tcp_congestion_control=" + cmd, shell=True, stdout=subprocess.PIPE)
        c.close()
        continue

    elif cmd == "Terminate!":
        subprocess.run("pkill iperf3", shell=True)
        c.close()
        s.close()
        break

    elif "Start!" in cmd:
        # Check cc
        subprocess.run("sysctl -a | grep 'net.ipv4.tcp_congestion_control'", shell=True)

        if id == -1:
            subprocess.run("iperf3 -s -p 5001 &", shell=True)
            id = 1

    c.close()