#!/usr/bin/python3

"""
Mininet iperf test between two hosts
"""

from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo, Topo
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.examples.linuxrouter import LinuxRouter
import time
import subprocess
import csv
import datetime
import multiprocessing


# todo Check where mininet does TC; what should be the limit value
class RTopo(Topo):
    #def __init__(self, **kwargs):
    #global r
    def build(self, **_opts):
        defaultIP = '10.0.1.1/24'
        r  = self.addNode('r', cls=LinuxRouter, ip=defaultIP)
        h1 = self.addHost('h1', ip='10.0.1.10/24', defaultRoute='via 10.0.1.1')
        h2 = self.addHost('h2', ip='10.0.2.10/24', defaultRoute='via 10.0.2.1')

        self.addLink(h1, r, intfName1 = 'h1-eth', intfName2 = 'r-eth1', params2 = {'ip' : '10.0.1.1/24'})
        self.addLink(h2, r, intfName1 = 'h2-eth', intfName2 = 'r-eth2', params2 = {'ip' : '10.0.2.1/24'})


def iperfTest():
    topo = RTopo()
    net = Mininet(topo=topo)
    net.start()
    h1 = net['h1']
    h2 = net['h2']
    r = net['r']

    # Let h1 send data to h2 -- configure tc on r-eth2 (egress to h2)
    IF = 'r-eth2'
    MTU = 1500

    r.cmd('tc qdisc add dev ' + IF + ' root handle 1:0 netem delay ' + str(delay) + 'ms')
    r.cmd('tc qdisc add dev ' + IF + ' parent 1:1 handle 10: tbf rate ' + str(bw) + 'mbit' + \
                ' burst ' + str(burst) + ' limit ' + str(limit))

    linkDelay = delay + rtprop
    h1.cmd('ethtool -K h1-eth tx off')
    r.cmd('ethtool -K r-eth1 lro off gro off')
    r.cmd('ethtool -K r-eth2 lro off gro off')
    bdp = int(bw * 1e6 / 8 * linkDelay / 1e3)

    print('\n')
    print(['bdp', convertSize(bdp), 'buffer', convertSize(limit)])
    print(['cc: ', cc, 'delay', str(linkDelay), 'bw', bw, 'limit', limit, 'burst', burst])
    print(r.cmd('tc qdisc show dev r-eth2'))

    iperf_server = h1.cmd('iperf3 -s -p 5001&')
    iperf_client = h2.cmd('iperf3 -c 10.0.1.10 -t ' + str(t) + ' -i 1 -p 5001 -R')

    h1.cmd('pkill iperf3')
    h2.cmd('pkill iperf3')
    print(iperf_client)

    # Save the experimental logs to file
    logfile = open(logname, 'a+')
    print(['cc: ', cc, 'delay', str(linkDelay), 'bw', bw, 'limit', limit, 'burst', burst], file=logfile)
    print(iperf_client, file=logfile)
    logfile.close()

    retr = int(iperf_client.splitlines()[-4].split()[8])
    goodput = float(iperf_client.splitlines()[-3].split()[-3])
    unit = iperf_client.splitlines()[-3].split()[-2]

    if unit == "Gbits/sec":
        goodput *= 1e9
    elif unit == "Mbits/sec":
        goodput *= 1e6
    elif unit == "Kbits/sec":
        goodput *= 1e3
    elif unit == "bits/sec":
        pass

    if goodput > 0:
        loss = retr / (goodput * t / 8 / MTU) * 100
    else:
        loss = 100

    record = [cc, linkDelay, bw, limit, burst, retr, convertSize(bdp), convertSize(limit), loss, goodput]

    csvfile = open(csvname, 'a+')
    writer = csv.writer(csvfile)
    writer.writerow(record)
    csvfile.close()

    net.stop()
    print('Success!' + ' -- ' + str(record))


def convertSize(num):
    cnt = 0
    while num >= 1000:
        num /= 1000
        cnt += 3

    unit = [0] * 9

    for i in range(3):
        unit[i] = 'b'
    for i in range(3, 6):
        unit[i] = 'kb'
    for i in range(6, 9):
        unit[i] = 'mb'
    return str(int(num)) + unit[cnt]


if __name__ == '__main__':
    ccs = ['bbr', 'cubic'] # 2 values
    delays = [0, 1, 5, 10, 25, 50, 75, 100, 150, 200] # 10 values
    bws = [1, 10, 100, 1000, 10000] # 5 values
    bursts = [1000000] # 1 value
    limits = [1000, 2000, 5000, 10000, 500000, 1000000, 2000000, 5000000, 10000000, 100000000] # 10 values

    '''
    In total, we have 2*10*5*10 = 1000 combinations. Each exp takes 10s -> 10000s ~ 3hrs.
    '''

    d = datetime.datetime.now()

    csvname = "tbf-exp-" + "{:%y%m%d_%H%M%S}".format(d) + ".csv"
    csvfile = open(csvname, 'a+')
    writer = csv.writer(csvfile)
    writer.writerow(['CC', ' Delay', ' BW', ' Limit', ' Burst', ' Retr', ' BDP', ' Buffer', ' Loss(%)', ' Goodput(bps)'])
    csvfile.close()

    logname = "tbf-exp-" + "{:%y%m%d_%H%M%S}".format(d) + ".log"
    logfile = open(logname, 'a+')
    logfile.close()

    t = 10
    to = 2
    rtprop = 0.033

    for cc in ccs:
        print("Switching congestion control to: " + cc)
        subprocess.run("sysctl -w net.ipv4.tcp_congestion_control=" + cc, shell=True)

        for bw in bws:
            for delay in delays:
                for limit in limits:
                    for burst in bursts:
                        p = multiprocessing.Process(target=iperfTest)
                        start = time.time()
                        p.start()
                        p.join(t + to)
                        end = time.time()
                        print('Elaspe time: ' + str(end - start) + 's')

                        if p.is_alive():
                            print('Experiment failed...')
                            p.terminate()
