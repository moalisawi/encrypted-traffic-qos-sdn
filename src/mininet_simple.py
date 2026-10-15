# mininet_simple.py — Topology with QoS queues (Scenario C)
#
# One OVS switch (OpenFlow 1.3), five hosts, three HTB queues on s1-eth1,
# remote Ryu controller on 127.0.0.1:6633.
#
# Run:  sudo python3 src/mininet_simple.py
import subprocess
import time

from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController

QOS_CMD = """ovs-vsctl -- \
    set port s1-eth1 qos=@newqos -- \
    --id=@newqos create qos type=linux-htb \
    queues=1=@q1,2=@q2,3=@q3 -- \
    --id=@q1 create queue other-config:min-rate=5000000 \
                      other-config:max-rate=10000000 -- \
    --id=@q2 create queue other-config:min-rate=3000000 \
                      other-config:max-rate=10000000 -- \
    --id=@q3 create queue other-config:min-rate=500000 \
                      other-config:max-rate=2000000"""


def create_topology(with_qos=True):
    setLogLevel('info')

    net = Mininet(controller=RemoteController,
                  switch=OVSSwitch, autoSetMacs=True)

    net.addController('c0', controller=RemoteController,
                      ip='127.0.0.1', port=6633)
    s1 = net.addSwitch('s1', protocols='OpenFlow13')

    h1 = net.addHost('h1', ip='10.0.0.1/24')  # VoIP
    h2 = net.addHost('h2', ip='10.0.0.2/24')  # Video
    h3 = net.addHost('h3', ip='10.0.0.3/24')  # Web
    h4 = net.addHost('h4', ip='10.0.0.4/24')  # File transfer
    h5 = net.addHost('h5', ip='10.0.0.5/24')  # Gaming

    for h in (h1, h2, h3, h4, h5):
        net.addLink(h, s1)

    net.start()
    time.sleep(2)
    subprocess.call("ovs-vsctl set bridge s1 protocols=OpenFlow13",
                    shell=True)

    print("\n[*] Testing connectivity...")
    net.pingAll()  # MUST run before QoS (FR-08)

    if with_qos:
        print("\n[*] Adding QoS queues...")
        subprocess.call(QOS_CMD, shell=True)
        print("[*] QoS queues added")

    print("\nmininet CLI ready")
    print("Hosts: h1(VoIP) h2(Video) h3(Web) h4(FileTransfer) h5(Gaming)")
    CLI(net)
    net.stop()


if __name__ == '__main__':
    create_topology(with_qos=True)
