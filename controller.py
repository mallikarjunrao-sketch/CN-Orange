import eventlet
eventlet.monkey_patch()

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp, icmp


class TrafficClassifier(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TrafficClassifier, self).__init__(*args, **kwargs)
        self.stats = {"TCP": 0, "UDP": 0, "ICMP": 0}

    # Send ALL packets to controller
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER,
                                          ofp.OFPCML_NO_BUFFER)]

        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(
            datapath=dp,
            priority=0,
            match=match,
            instructions=inst
        )
        dp.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser

        pkt = packet.Packet(msg.data)

        # CLASSIFICATION
        if pkt.get_protocol(tcp.tcp):
            self.stats["TCP"] += 1
            print("TCP detected")

        elif pkt.get_protocol(udp.udp):
            self.stats["UDP"] += 1
            print("UDP detected")

        elif pkt.get_protocol(icmp.icmp):
            self.stats["ICMP"] += 1
            print("ICMP detected")

        print(self.stats)

        # ALWAYS FLOOD (so network works)
        actions = [parser.OFPActionOutput(ofp.OFPP_FLOOD)]

        out = parser.OFPPacketOut(
            datapath=dp,
            buffer_id=ofp.OFP_NO_BUFFER,
            in_port=msg.match['in_port'],
            actions=actions,
            data=msg.data
        )
        dp.send_msg(out)
