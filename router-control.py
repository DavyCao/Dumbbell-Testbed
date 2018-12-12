import socket
import subprocess
import time

#loss = [1, 0.1, 0.01, 0.001]
#delay = [5, 10, 20, 50, 100, 200]
#bw = [10, 100, 200, 500, 1000]

loss = [0.1]
delay = [5]
bw = [100, 900]

for i in loss:
	for j in delay:
		for k in bw:
			cmd = "./set-network " + str(i) + " " + str(j) + " " + str(k)
			subprocess.run(cmd, shell=True)

			# Check the configs
			qdiscConfig = subprocess.run("tc qdisc show dev ifb0", shell=True, stdout=subprocess.PIPE).stdout
			classConfig = subprocess.run("tc class show dev ifb0", shell=True, stdout=subprocess.PIPE).stdout

			if len(qdiscConfig) == 0:
				qdiscConfig = "No qdisc config!\n".encode()
			if len(classConfig) == 0:
				classConfig = "No class config!\n".encode()

			# Send instructions to Server3 -- sender
			s3 = socket.socket()
			s3.connect(('192.168.3.2', 6001))
			s3.sendall(qdiscConfig)
			s3.sendall(classConfig)
			s3.sendall("Start!".encode())
			s3.close()

			time.sleep(1)

			# Send instructions to Server2 -- receiver
			s2 = socket.socket()
			s2.connect(('192.168.2.2', 6001))
			#s2.sendall(qdiscConfig)
			#s2.sendall(classConfig)
			s2.sendall("Start!".encode())

			#print(qdiscConfig.decode())
			#print(classConfig.decode())
			print("Loss: " + str(i) + "%; Delay: " + str(j) + "ms; BW: " + str(k) + "mbps")

			msg = s2.recv(1024).decode()
			print(msg)
			s2.close()

# Terminate Server2 and Server3 Listener
s2 = socket.socket()
s2.connect(('192.168.2.2', 6001))
s2.sendall("Terminate!".encode())
s2.close()

s3 = socket.socket()
s3.connect(('192.168.3.2', 6001))
s3.sendall("Terminate!".encode())
s3.close()

subprocess.run("./clean-tc", shell=True)
print("Experiments finish!")