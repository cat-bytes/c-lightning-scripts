#!/usr/bin/python3
import re
from pyln.client import LightningRpc
from os.path import expanduser

# Get list of all channels to exclude from source node except destination channel
#
def getExcludes(rpc, destination):

    info = rpc.getinfo()
    channels = rpc.listchannels(source=info["id"])
    excludes = []
    for channel in channels["channels"]:
#        print(channel["short_channel_id"])
        if destination == channel["destination"]:
            print(channel["destination"])
        else:
            excludes.append(channel["destination"])
#    print(excludes)
#    excludes.remove(src_scid)
#    excludes.remove(dest_scid)
    return excludes

if __name__ == "__main__":
    rpc = LightningRpc(expanduser("~") + "/.lightning/bitcoin/lightning-rpc")
    # Wallet of Satoshi (test)
    destination = "035e4ff418fc8b5554c5d9eea66396c227bd429a3251c8cbc711002ba215bfc226"
    excluded = getExcludes(rpc, destination)
    print(excluded)
