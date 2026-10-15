# ryu_qos_controller.py — SDN controller with ML-driven per-flow QoS
#
# Learning switch on OpenFlow 1.3 that classifies each flow with the
# Random Forest model and installs a flow rule carrying OFPActionSetQueue,
# steering the flow into its HTB queue on the OVS switch.
#
# Run (Python 3.9, Ryu 4.34):
#   python3.9 -m ryu.cmd.manager src/ryu_qos_controller.py
import os
import time

import joblib
import numpy as np
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import ethernet, packet
from ryu.ofproto import ofproto_v1_3

PROJECT_DIR = os.environ.get(
    'PROJECT_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(PROJECT_DIR, 'model')

# Queue IDs for QoS
QUEUE_MAP = {
    'VoIP': 1,             # Highest priority: 5-10 Mbps guaranteed
    'Video_Streaming': 2,  # 3-10 Mbps
    'Web_Browsing': 2,     # 3-10 Mbps
    'Gaming': 2,           # 3-10 Mbps
    'File_Transfer': 3,    # Lowest priority: 0.5-2 Mbps
}


class QoSController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(QoSController, self).__init__(*args, **kwargs)
        self.model = joblib.load(os.path.join(MODEL_DIR, 'model.pkl'))
        self.features = joblib.load(os.path.join(MODEL_DIR, 'features.pkl'))
        self.mac_to_port = {}
        self.flow_stats = {}
        self.logger.info("QoS Controller started — ML model loaded")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # Table-miss entry — PERMANENT (DF-01 fix: idle=0, hard=0).
        # This rule must never expire, otherwise the switch stops
        # forwarding unmatched packets to the controller after 120 s.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions,
                      idle_timeout=0, hard_timeout=0)
        self.logger.info("Switch connected: %s", datapath.id)

    def add_flow(self, datapath, priority, match, actions, queue_id=None,
                 idle_timeout=30, hard_timeout=120):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        if queue_id is not None:
            actions = [parser.OFPActionSetQueue(queue_id)] + actions
        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst,
                                idle_timeout=idle_timeout,
                                hard_timeout=hard_timeout)
        datapath.send_msg(mod)

    def classify_flow(self, pkt_count, byte_count, duration):
        # OpenFlow exposes 3 of the 23 training features live; they are the
        # three most important features of the model. The rest stay zero.
        feature_vector = np.zeros(len(self.features))
        feat_dict = {
            'duration': duration,
            'flowPktsPerSecond': pkt_count / max(duration, 1),
            'flowBytesPerSecond': byte_count / max(duration, 1),
        }
        for i, f in enumerate(self.features):
            if f in feat_dict:
                feature_vector[i] = feat_dict[f]
        return self.model.predict([feature_vector])[0]

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst, src = eth.dst, eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)
        actions = [parser.OFPActionOutput(out_port)]

        # Per-flow packet and byte counters
        flow_key = (src, dst)
        now = time.time()
        if flow_key not in self.flow_stats:
            self.flow_stats[flow_key] = {'start': now, 'pkts': 0, 'bytes': 0}
        self.flow_stats[flow_key]['pkts'] += 1
        self.flow_stats[flow_key]['bytes'] += len(msg.data)
        duration = now - self.flow_stats[flow_key]['start']

        # Classify every tenth packet and install a queued flow rule
        if self.flow_stats[flow_key]['pkts'] % 10 == 0:
            traffic_class = self.classify_flow(
                self.flow_stats[flow_key]['pkts'],
                self.flow_stats[flow_key]['bytes'], duration)
            queue_id = QUEUE_MAP.get(traffic_class, 2)
            self.logger.info("Flow %s->%s: %s → Queue %d",
                             src, dst, traffic_class, queue_id)
            if out_port != ofproto.OFPP_FLOOD:
                match = parser.OFPMatch(in_port=in_port,
                                        eth_dst=dst, eth_src=src)
                self.add_flow(datapath, 1, match, actions, queue_id)

        data = msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=msg.buffer_id,
                                  in_port=in_port,
                                  actions=actions, data=data)
        datapath.send_msg(out)
