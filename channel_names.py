
from pyln.client import LightningRpc

# Create short_channel_id to node_alias mapping
#
def getChannelNames(rpc):

    info = rpc.getinfo()
    channels = rpc.listchannels(source=info["id"])
    short_channels = []
    for channel in channels["channels"]:
        source = rpc.listnodes(channel["source"])
        src_node = source["nodes"][0]
        destination = rpc.listnodes(channel["destination"])
        dest_node = destination["nodes"][0]
        chan_info = { 'short_channel_id': channel["short_channel_id"], 'node_alias': dest_node["alias"] }
        short_channels += [chan_info]
        print(chan_info)
    return short_channels

