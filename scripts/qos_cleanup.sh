#!/usr/bin/env bash
# Remove QoS records and stale Mininet state after testing
ovs-vsctl clear port s1-eth1 qos
ovs-vsctl -- --all destroy qos -- --all destroy queue
sudo mn -c
