#!/usr/bin/python3
import re
from pyln.client import LightningRpc
from os.path import expanduser

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
        if "alias" in dest_node:
            chan_info = { 'short_channel_id': channel["short_channel_id"], 'node_alias': re.sub(r'[^a-zA-Z0-9_\. \[\]()/-]+', '', dest_node["alias"]) }
        else:
            chan_info = { 'short_channel_id': channel["short_channel_id"], 'node_alias': dest_node["nodeid"][:12] }
        short_channels += [chan_info]
        print(chan_info)
    return short_channels

if __name__ == "__main__":
    rpc = LightningRpc(expanduser("~") + "/.lightning/bitcoin/lightning-rpc")
    getChannelNames(rpc)
