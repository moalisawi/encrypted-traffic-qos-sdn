# Raw Test Results

These are the ping summary lines, unedited, produced on 6 July 2026. Every trial is 30 ICMP probes from h1. In the congestion scenarios, a 35-second iperf TCP stream h3 → h4 provides the load.

## Scenario A — Baseline (no load, no QoS)

```
mininet> h1 ping h2 -c 30
30 packets transmitted, 30 received, 0% packet loss, time 29569ms
rtt min/avg/max/mdev = 0.032/1.247/27.238/4.868 ms

mininet> h1 ping h4 -c 30
30 packets transmitted, 30 received, 0% packet loss, time 29660ms
rtt min/avg/max/mdev = 0.036/1.804/26.880/6.534 ms

mininet> h1 ping h5 -c 30
30 packets transmitted, 30 received, 0% packet loss, time 29592ms
rtt min/avg/max/mdev = 0.036/1.225/26.210/4.688 ms
```

## Scenario B — Congestion without QoS

```
mininet> h4 iperf -s &
mininet> h3 iperf -c 10.0.0.4 -t 35 &

mininet> h1 ping h2 -c 30
30 packets transmitted, 30 received, 0% packet loss, time 29541ms
rtt min/avg/max/mdev = 0.029/5.754/82.704/18.714 ms

mininet> h1 ping h4 -c 30
30 packets transmitted, 30 received, 0% packet loss, time 29541ms
rtt min/avg/max/mdev = 0.037/2.180/51.901/9.260 ms

mininet> h1 ping h5 -c 30
30 packets transmitted, 30 received, 0% packet loss, time 29555ms
rtt min/avg/max/mdev = 0.037/2.153/26.878/6.479 ms
```

## Scenario C — Congestion with QoS (HTB queues + classifier)

```
mininet> h4 iperf -s &
mininet> h3 iperf -c 10.0.0.4 -t 35 &

mininet> h1 ping h2 -c 30
30 packets transmitted, 30 received, 0% packet loss, time 29553ms
rtt min/avg/max/mdev = 0.025/3.405/80.070/14.329 ms

mininet> h1 ping h4 -c 30
30 packets transmitted, 30 received, 0% packet loss, time 29531ms
rtt min/avg/max/mdev = 0.038/1.205/26.119/4.665 ms

mininet> h1 ping h5 -c 30
30 packets transmitted, 30 received, 0% packet loss, time 29554ms
rtt min/avg/max/mdev = 0.032/1.151/25.447/4.546 ms
```

## Defect DF-01: expiring table-miss rule

Before the fix, the table-miss entry carried the same 30 s / 120 s timeouts as the per-flow rules. Once it expired, the switch stopped sending unmatched packets to the controller:

```
mininet> h1 ping h4 -c 30
30 packets transmitted, 0 received, +21 errors, 100% packet loss

mininet> sh ovs-ofctl -O OpenFlow13 dump-flows s1
(empty — table-miss rule had expired)
```

After the fix (table-miss installed with `idle_timeout=0, hard_timeout=0`):

```
mininet> h1 ping h4 -c 5
5 packets transmitted, 5 received, 0% packet loss, time 4006ms
rtt min/avg/max/mdev = 1.309/1.352/1.442/0.050 ms
```

## Connectivity and throughput

```
mininet> pingall
*** Results: 0% dropped (20/20 received)

mininet> h2 iperf -s &
mininet> h1 iperf -c 10.0.0.2 -t 10
[ 1] 0.0000-10.0058 sec 20.2 GBytes 17.4 Gbits/sec
```
