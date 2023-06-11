#!/usr/bin/env python3

import sys
from pyln.client import LightningRpc
from datetime import datetime
from os.path import expanduser
from channel_names import *


rpc = LightningRpc(expanduser("~") + "/.lightning/bitcoin/lightning-rpc")

epoch_begin = int(sys.argv[1])
epoch_end = int(sys.argv[2])

short_channels = getChannelNames(rpc)

invoices = rpc.listinvoices()

for invoice in invoices["invoices"]:
    if invoice["status"] == "paid":
       pay_time = int(invoice["paid_at"])
       if (invoice["label"].count("Rebalance-") > 0 and pay_time >= epoch_begin and pay_time <= epoch_end):
          descr = invoice["description"]
          rebal_route = descr.split(" to ", 2)
          if ((next((x for x in short_channels if x["short_channel_id"] == rebal_route[0]), None)) and
             (next((x for x in short_channels if x["short_channel_id"] == rebal_route[1]), None))):
#             print("from " + rebal_route[0] + " to " + rebal_route[1])
             chan_from = list(filter(lambda x: x["short_channel_id"] == rebal_route[0], short_channels))
             chan_to = list(filter(lambda x: x["short_channel_id"] == rebal_route[1], short_channels))
             dt_obj = datetime.fromtimestamp(invoice["paid_at"])
#             amount_msat = invoice["amount_msat"]
             transactions = rpc.listsendpays(payment_hash=invoice["payment_hash"])
             transact = transactions["payments"]
#             print(transact)
#             print(str(amount_msat) + " " + str(transact[0]["msatoshi"]) + " " + str(transact[0]["msatoshi_sent"]))
#             amount_msat = transact[0]["msatoshi"]
             amount_msat = transact[0]["amount_msat"]
#             sent_msat = transact[0]["msatoshi_sent"]
             sent_msat = transact[0]["amount_sent_msat"]
             print(dt_obj.strftime("%m/%d/%Y %H:%M:%S") + "  amount_msat = " + str(amount_msat / 1000.0) + " fee = " + str((sent_msat - amount_msat) / 1000.0) + " from " + chan_from[0]["node_alias"] + " to " + chan_to[0]["node_alias"])

