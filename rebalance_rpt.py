#!/usr/bin/env python3

# below is from pylightning => new package is pyln-client

from pyln.client import LightningRpc
from datetime import datetime
from channel_names import *


#def getChannelNames(rpc):

#    channels = rpc.listchannels(source=info["id"])
#    short_channels = []
#    for channel in channels["channels"]:
#        source = rpc.listnodes(channel["source"])
#        src_node = source["nodes"][0]
#        destination = rpc.listnodes(channel["destination"])
#        dest_node = destination["nodes"][0]
#        chan_info = { 'short_channel_id': channel["short_channel_id"], 'node_alias': dest_node["alias"] }
#        short_channels += [chan_info]
#        print(chan_info)
#    return short_channels


rpc = LightningRpc("/home/bitcoin/.lightning/bitcoin/lightning-rpc")

#info = rpc.getinfo()

short_channels = getChannelNames(rpc)

invoices = rpc.listinvoices()

for invoice in invoices["invoices"]:
    if (invoice["label"].count("Rebalance-") > 0 and invoice["status"] == "paid"):
       descr = invoice["description"]
       rebal_route = descr.split(" to ", 2)
       if ((next((x for x in short_channels if x["short_channel_id"] == rebal_route[0]), None)) and
          (next((x for x in short_channels if x["short_channel_id"] == rebal_route[1]), None))):
#          print("from " + rebal_route[0] + " to " + rebal_route[1])
          chan_from = list(filter(lambda x: x["short_channel_id"] == rebal_route[0], short_channels))
          chan_to = list(filter(lambda x: x["short_channel_id"] == rebal_route[1], short_channels))
          dt_obj = datetime.fromtimestamp(invoice["paid_at"])
#          amount_msat = invoice["amount_msat"]
          transactions = rpc.listsendpays(payment_hash=invoice["payment_hash"])
          transact = transactions["payments"]
#          print(str(amount_msat) + " " + str(transact[0]["msatoshi"]) + " " + str(transact[0]["msatoshi_sent"]))
          amount_msat = transact[0]["msatoshi"]
          sent_msat = transact[0]["msatoshi_sent"]
          print(dt_obj.strftime("%m/%d/%Y %H:%M:%S") + "  amount_msat = " + str(amount_msat / 1000.0) + " fee = " + str((sent_msat - amount_msat) / 1000.0) + " from " + chan_from[0]["node_alias"] + " to " + chan_to[0]["node_alias"])

