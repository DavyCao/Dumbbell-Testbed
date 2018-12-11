import subprocess
import socket

#loss = [1, 0.1, 0.01, 0.001]
#delay = [5, 10, 20, 50, 100, 200]
#bw = [10, 100, 200, 500, 1000]

loss = [0.001]
delay = [5, 10]
bw = [900]

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

			# Send instructions to S1
			s1 = socket.socket()
			s1.connect(('192.168.2.2', 6001))
			s1.sendall(qdiscConfig)
			s1.sendall(classConfig)
			s1.sendall("Start!".encode())
			s1.close()

			# Send instructions to S2
			s2 = socket.socket()
			s2.connect(('192.168.3.2', 6001))
			s2.sendall(qdiscConfig)
			s2.sendall(classConfig)
			s2.sendall("Start!".encode())
			
			print(qdiscConfig.decode())
			print(classConfig.decode())
			
			msg = s2.recv(1024).decode()
			print(msg)
			s2.close()

subprocess.run("./clean-tc", shell=True)
