import socket
import subprocess
import time
import datetime
import csv

cong = ["cubic", "bbr"]
loss = [0, 0.001, 0.01, 0.1, 1]
delay = [0, 10, 20, 50, 100, 200]
bw = [10, 100, 200, 500, 1000]

# cong = ["cubic", "bbr"]
# loss = [0.1]
# delay = [5]
# bw = [100, 900]

d = datetime.datetime.now()
logname = "/tmp/experiment_logs/Exp_" + "{:%y%m%d_%H%M%S}".format(d) + ".log"

csvname = "/tmp/experiment_logs/Exp_" + "{:%y%m%d_%H%M%S}".format(d) + ".csv"
csvfile = open(csvname, 'a+')
writer = csv.writer(csvfile)
writer.writerow(['Cong', 'Loss (%)', 'Delay (ms)', 'BW (mbps)', 'Actual Loss (%)', 'Actual BW (mbps)'])
csvfile.close()

for c in cong:
	# Set congestion control
	s2 = socket.socket()
	s2.connect(('192.168.2.2', 6001))
	s2.sendall(c.encode())
	s2.close()

	s3 = socket.socket()
	s3.connect(('192.168.3.2', 6001))
	s3.sendall(c.encode())
	s3.close()

	for i in loss:
		for j in delay:
			for k in bw:
				try:
					logfile = open(logname, 'a+')

					print("")
					cmd = "./set-network " + str(i) + " " + str(j) + " " + str(k)
					subprocess.run(cmd, shell=True)

					# Check the configs
					qdiscConfig = subprocess.run("tc qdisc show dev ifb0", shell=True, stdout=subprocess.PIPE).stdout
					classConfig = subprocess.run("tc class show dev ifb0", shell=True, stdout=subprocess.PIPE).stdout

					if len(qdiscConfig) == 0:
						qdiscConfig = "No qdisc config!\n".encode()
					if len(classConfig) == 0:
						classConfig = "No class config!\n".encode()

					msg_snd = qdiscConfig + "\n".encode() + classConfig + "\nStart!".encode()

					# Send instructions to Server3 -- sender
					s3 = socket.socket()
					s3.connect(('192.168.3.2', 6001))
					s3.sendall(msg_snd)
					s3.close()

					time.sleep(1)

					# Send instructions to Server2 -- receiver
					s2 = socket.socket()
					s2.connect(('192.168.2.2', 6001))
					s2.sendall(msg_snd)

					print("Cong: " + c + "; Loss: " + str(i) + "%; Delay: " + str(j) + "ms; BW: " + str(k) + "mbps", file=logfile)

					msg_recv = s2.recv(1024).decode()
					print(msg_recv, file=logfile)
					s2.close()
					
					actualBW = float(msg_recv.split()[-3])
					lossNum = float(msg_recv.split()[8])
					transferTime = float(msg_recv.split()[-7].split('-')[1])

					unit = msg_recv.split()[-2]
					if unit == "Gbits/sec":
						sndBytes = (transferTime * actualBW) / 8 * 1e9
					elif unit == "Mbits/sec":
						sndBytes = (transferTime * actualBW) / 8 * 1e6
					elif unit == "Kbits/sec":
						sndBytes = (transferTime * actualBW) / 8 * 1e3
					elif unit == "bits/sec":
						sndBytes = (transferTime * actualBW) / 8
					pktNum = sndBytes / 1448

					actualLoss = lossNum / pktNum * 100

					record = [i, j, k, actualLoss, actualBW]
					record = ['%.3f' % a for a in record]
					record.insert(0, c)

					csvfile = open(csvname, 'a+')
					writer = csv.writer(csvfile)
					writer.writerow(record)
					csvfile.close()
					logfile.close()

				except Exception as e:
					print(e, file=logfile)
					csvfile.close()
					logfile.close()

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
