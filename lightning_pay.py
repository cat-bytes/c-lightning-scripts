#!/usr/bin/python3

import argparse
import os
import sys
import json
from os.path import expanduser
from pyln.client import LightningRpc
from channel_exclude import *


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("bolt11_or_destination_id")
parser.add_argument("-use_sendpay", default="no", type=str, nargs="?")
parser.add_argument("-scid_out", type=str, nargs="?")
parser.add_argument("amount_in_milli_satoshi", default=None, type=int, nargs="?")
parser.add_argument("payment_hash", nargs="?")
parser.add_argument("min_final_cltv_expiry", nargs="?")
args = parser.parse_args()


rpc_path = expanduser("~") + "/.lightning/bitcoin/lightning-rpc"

ld = LightningRpc(rpc_path)

assert len(args.bolt11_or_destination_id) > 2, "argument bolt11_or_destination_id is invalid"

# Bolt11 passed if prefix is 'ln'
use_bolt11 = args.bolt11_or_destination_id[:2] == "ln"

if use_bolt11:
    bolt11 = ld.decodepay(args.bolt11_or_destination_id)
    print(bolt11)
    #print("Bolt11 decoded:\n%s" % json.dumps(bolt11, indent=4))
    id_ = bolt11["payee"]


    payment_hash = bolt11["payment_hash"]
    print("id = " + id_ + "  payment_hash = " + payment_hash)
#    if "msatoshi" in bolt11:
    if "amount_msat" in bolt11:
        amount_included_in_bolt = True
#        amount = bolt11["msatoshi"]
        amount = bolt11["amount_msat"]
    else:
        assert args.amount_in_milli_satoshi, "need argument amount_in_milli_satoshi"
        amount = args.amount_in_milli_satoshi
        amount_included_in_bolt = False


    if args.use_sendpay == 'yes':
        print("using sendpay")
        payment_secret = bolt11["payment_secret"]
        min_cltv_expiry = bolt11["min_final_cltv_expiry"]
        
        print(id_)
        out_chan = id_
#        if args.scid_out is not None:
#            print(args.scid_out)
#            output = ld.listchannels(args.scid_out)
#            chan = output["channels"]
#            print(chan[0])
#            print(chan[1])
#            out_chan = chan[1]["destination"]
#            route = ld.getroute(id_, amount, fromid=out_chan, riskfactor=100, cltv=min_cltv_expiry)
#            delay = route["route"][0]["delay"]
#            fee = route["route"][0]["msatoshi"] - amount
#            print(delay)
#            print(output)

#        print(out_chan)

        excludes = getExcludes(ld, out_chan)
#        output = ld.getroute(out_chan, amount, maxhops=1, riskfactor=100, cltv=min_cltv_expiry, exclude=excludes)
#        leg = output["route"][0]
#        leg["delay"] = leg["delay"] + delay
#        leg["msatoshi"] = leg["msatoshi"] + fee + 2000
#        leg["amount_msat"] = leg["amount_msat"] + fee + 2000
#        print(leg)
#        route["route"].insert(0, leg)

        route = ld.getroute(id_, amount, maxhops=1, riskfactor=100, cltv=min_cltv_expiry, exclude=excludes)
        print(route)
#        exit()
#        fee = route["route"][0]["msatoshi"] - amount
        fee = route["route"][0]["amount_msat"] - amount

        reply = input("Paying fee %s on amount %s (%.3f%%). Send [Y/n]? " % (fee, amount, fee / amount * 100.0))

        if reply in ["y", "Y"]:
            ld.sendpay(route["route"], payment_hash, payment_secret=payment_secret)
        else:
            print("Not sending.")
    else:
        reply = input("Pay %s msatoshi [Y/n]? " % amount)

        if reply in ["y", "Y"]:
            if amount_included_in_bolt:
                ld.pay(args.bolt11_or_destination_id)
            else:
                ld.pay(args.bolt11_or_destination_id, amount)
        else:
            print("Not sending.")

else:
    assert args.amount_in_milli_satoshi, "need argument amount_in_milli_satoshi"
    assert args.payment_hash, "need argument payment_hash"
    assert args.min_final_cltv_expiry, "need argument min_final_cltv_expiry"
    amount = args.amount_in_milli_satoshi
    id_ = args.bolt11_or_destination_id
    payment_hash = args.payment_hash
    min_cltv_expiry = args.min_final_cltv_expiry

    route = ld.getroute(id_, amount, 1, min_cltv_expiry)
    print(route)
    fee = route["route"][0]["msatoshi"] - amount

    reply = input("Paying fee %s on amount %s (%.3f%%). Send [Y/n]? " % (fee, amount, fee / amount * 100.0))

    if reply in ["y", "Y"]:
        ld.sendpay(route["route"], payment_hash)
    else:
        print("Not sending.")
        sys.exit(1)
