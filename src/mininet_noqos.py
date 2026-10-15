# mininet_noqos.py — Same topology without HTB queues (Scenarios A and B)
#
# Run:  sudo python3 src/mininet_noqos.py
from mininet_simple import create_topology

if __name__ == '__main__':
    create_topology(with_qos=False)
