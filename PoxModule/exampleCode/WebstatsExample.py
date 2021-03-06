import pox.openflow.libopenflow_01 as of
from pox.core import core
import time
log = core.getLogger("WebStats")
 
# When we get flow stats, print stuff out
def handle_flow_stats (event):
    web_bytes = 0
    web_flows = 0
    for f in event.stats:
        if f.match.tp_dst == 80 or f.match.tp_src == 80:
            web_bytes += f.byte_count
            web_flows += 1
    log.info("Web traffic: %s bytes over %s flows", web_bytes, web_flows)
 
# Listen for flow stats
core.openflow.addListenerByName("FlowStatsReceived", handle_flow_stats)

# Now actually request flow stats from all switches
for con in core.openflow.connections: # make this _connections.keys() for pre-betta
    con.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))