import socket
import subprocess

s = socket.socket()
s.bind(('0.0.0.0', 6001))
s.listen(5)
while True:
	c, addr = s.accept()
	print("Got connection from", addr)
	cmd = c.recv(1024).decode()
	print(cmd)
	if "Start!" in cmd:
		subprocess.run("iperf3 -c 192.168.2.2 -t 60 -i 1 -R -p 5001", shell=True)
	c.sendall("Finish!".encode())
	c.close()