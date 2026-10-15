#!/usr/bin/env bash
# HTB QoS provisioning on s1-eth1 (normally done by src/mininet_simple.py)
set -e

# Force OpenFlow 1.3 on the bridge
ovs-vsctl set bridge s1 protocols=OpenFlow13

# Q1: VoIP 5-10 Mbps · Q2: Video/Web/Gaming 3-10 Mbps · Q3: File transfer 0.5-2 Mbps
ovs-vsctl \
  -- set port s1-eth1 qos=@newqos \
  -- --id=@newqos create qos type=linux-htb queues=1=@q1,2=@q2,3=@q3 \
  -- --id=@q1 create queue other-config:min-rate=5000000 other-config:max-rate=10000000 \
  -- --id=@q2 create queue other-config:min-rate=3000000 other-config:max-rate=10000000 \
  -- --id=@q3 create queue other-config:min-rate=500000 other-config:max-rate=2000000

# Inspect installed flow rules
ovs-ofctl -O OpenFlow13 dump-flows s1
