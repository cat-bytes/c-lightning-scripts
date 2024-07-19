#!/usr/bin/python3
import sys
import json
import operator
import argparse
from datetime import date, datetime
from pyln.client import LightningRpc
from os.path import expanduser

# Specify ratio limits for draining (outgoing channel) and filling (incoming channel)
# when rebalancing

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# outgoing channel to remove balance from (drain)
parser.add_argument("-scid_out", type=str, nargs="?")

# incoming channel to balance (fill)
parser.add_argument("-scid_in", type=str, nargs="?")

# do not go below this ration on outgoing channel
parser.add_argument("-ratio_out", type=float, nargs="?")

# on incoming channel fill up to this ration
parser.add_argument("-ratio_in", type=float, nargs="?")
args = parser.parse_args()

rpc = LightningRpc(expanduser("~") + "/.lightning/bitcoin/lightning-rpc")

rebalance = False

info = rpc.getinfo()
channels_in = rpc.listchannels(args.scid_in)
channels_out = rpc.listchannels(args.scid_out)
if len(channels_in["channels"]) > 0 and len(channels_out["channels"]) >0:

    if channels_out["channels"][0]["destination"] == info["id"]:
        source = channels_out["channels"][0]["source"]
    else:
        source = channels_out["channels"][1]["source"]
#    print(source)

    # Only rebalance if source (scid_out) channel balance is greater than ratio_out
#    peers = rpc.listpeers(source)
#    peer = peers["peers"][0]
    peer = rpc.listpeerchannels(source)
    chan = peer["channels"][0]
    if ((chan["to_us_msat"] / chan["total_msat"])) > args.ratio_out:
        rebalance = True
    else:
        rebalance = False


    if channels_in["channels"][0]["source"] == info["id"]:
        destination = channels_in["channels"][0]["destination"]
    else:
        destination = channels_in["channels"][1]["destination"]

    # Only rebalance if target (scid_in) channel balance is less than ratio_in
#    peers = rpc.listpeers(destination)
#    peer = peers["peers"][0]
    peer = rpc.listpeerchannels(destination)
    chan = peer["channels"][0]
    if ((chan["to_us_msat"] / chan["total_msat"])) < args.ratio_in:
        rebalance = True
    else:
        rebalance = False


    # lowest maxfeepercent = 0.070
    # was 0.10, 0.15, 0.20
    if rebalance:
        rpc.rebalance(outgoing_scid=args.scid_out,incoming_scid=args.scid_in,msatoshi='250000sat',retry_for=180,maxfeepercent=0.20)

