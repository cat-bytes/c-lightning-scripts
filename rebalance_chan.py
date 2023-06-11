#!/usr/bin/python3
import sys
import json
import operator
import argparse
from datetime import date, datetime
from pyln.client import LightningRpc
from os.path import expanduser

# Specify ratio to rebalance up to when using rebalance plugin with individual channels

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-scid_out", type=str, nargs="?")
parser.add_argument("-scid_in", type=str, nargs="?")
parser.add_argument("-ratio", type=float, nargs="?")
args = parser.parse_args()

rpc = LightningRpc(expanduser("~") + "/.lightning/bitcoin/lightning-rpc")

info = rpc.getinfo()
channels = rpc.listchannels(args.scid_in)
if len(channels["channels"]) > 0:
    if channels["channels"][0]["source"] == info["id"]:
        destination = channels["channels"][0]["destination"]
    else:
        destination = channels["channels"][1]["destination"]

    peers = rpc.listpeers(destination)
    peer = peers["peers"][0]
    chan = peer["channels"][0]
    if ((chan["to_us_msat"] / chan["total_msat"])) < args.ratio:
        rpc.rebalance(outgoing_scid=args.scid_out,incoming_scid=args.scid_in,msatoshi='250000sat',retry_for=180,maxfeepercent=0.25)

