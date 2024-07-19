#!/usr/bin/python3
import sys
import json
import operator
from datetime import date, datetime
from pyln.client import LightningRpc
from os.path import expanduser
from channel_names import *

rpc = LightningRpc(expanduser("~") + "/.lightning/bitcoin/lightning-rpc")


channels = set() # a bag of scids
channel_fees_collected = dict() # scid -> (x, y) where x = fees from this channel as input, y = fees from this channel as output
msat_moved = dict() # scid -> ((n, x), (n, y)) where x = msat moved in all forwards with this channel as input, y = msat moved " as output and n in both cases is the number of forwarding events
rebalance_payment_hashes = set()
rebalance_msat_received = dict() # payment hash -> msat received
rebalance_channels = dict() # payment hash -> (x, y) where x = outgoing channel, y = incoming channel
channel_rebalance_paid = dict() #scid -> (x, y) where x = fees paid rebalancing this channel in, y = fees paid rebalancing this channel out
rebalance_fees = dict() # payment hash -> msat

def print_usage_and_die():
    sys.stderr.write("Usage:\n")
    sys.stderr.write("%s $(date '+%%s' -d \"Apr 01 2021\") $(date '+%%s' -d \"May 01 2021\")\n" % sys.argv[0])
    sys.stderr.write("\n")
    sys.stderr.write("Calculates your C-Lightning node's earnings and rebalancing costs in the specified period.\n")
    sys.stderr.write("\n")
    sys.stderr.write("Note that earnings and costs are double-reported, once for the incoming and once for the\n")
    sys.stderr.write("outgoing channel.")
    sys.stderr.write("\n")
    sys.exit(1)

if len(sys.argv) < 3:
    print_usage_and_die()

epoch_begin = int(sys.argv[1])
epoch_end = int(sys.argv[2])
epoch_begin_str = datetime.utcfromtimestamp(epoch_begin).strftime('%Y-%m-%d %H:%M:%S')
epoch_end_str = datetime.utcfromtimestamp(epoch_end).strftime('%Y-%m-%d %H:%M:%S')

if epoch_end <= epoch_begin:
    print_usage_and_die()

channel_aliases = getChannelNames(rpc)

for peer in rpc.listpeers()["peers"]:
    if len(peer["channels"]) > 0:
        chan = peer["channels"][0]
        try:
            scid = chan["short_channel_id"]
            channels.add(scid)
        except:
            pass

for invoice in rpc.listinvoices()["invoices"]:
    if invoice["status"] == "paid":
        pay_time = int(invoice["paid_at"])
        if invoice["label"].startswith("Rebalance-") and pay_time >= epoch_begin and pay_time <= epoch_end and len(invoice["description"].split(' to ')) == 2:
            payhash = invoice["payment_hash"]
            rebalance_payment_hashes.add(payhash)
            rebalance_channels[payhash] = tuple(invoice["description"].split(' to '))
            rebalance_msat_received[payhash] = invoice["amount_received_msat"]
for payment in rpc.listpays()["pays"]:
    payhash = payment["payment_hash"]
    if payhash in rebalance_payment_hashes:
        amount_sent = int(payment["amount_sent_msat"])
        amount_rcvd = int(rebalance_msat_received[payhash])
        fees_paid = amount_sent - amount_rcvd
        if amount_sent == 0:
            fees_paid = 0 # handle bugs: if we marked the invoice as paid but the payment failed
        rebalance_fees[payhash] = fees_paid
for payhash, (chan_out, chan_in) in rebalance_channels.items():
    fee = rebalance_fees[payhash]

    paid = (fee, 0)
    if chan_out in channel_rebalance_paid:
        paid = channel_rebalance_paid[chan_out]
        paid = (paid[0] + fee, paid[1])
    channel_rebalance_paid[chan_out] = paid    

    paid = (0, fee)
    if chan_in in channel_rebalance_paid:
        paid = channel_rebalance_paid[chan_in]
        paid = (paid[0], paid[1] + fee)
    channel_rebalance_paid[chan_in] = paid    

#get flow statistics:
for forward in rpc.listforwards()["forwards"]:
    fwd_time = forward["received_time"]
    if forward["status"] == "settled" and fwd_time >= epoch_begin and fwd_time <= epoch_end:
        in_scid = forward["in_channel"]
        out_scid = forward["out_channel"]
        fee = int(forward["fee_msat"])

        channels.add(in_scid)
        channels.add(out_scid)

        in_amt = int(forward["in_msat"])
        flow = ((1, in_amt), (0, 0))
        if in_scid in msat_moved:
            flow = msat_moved[in_scid]
            flow = ((flow[0][0] + 1, flow[0][1] + in_amt), flow[1])
        msat_moved[in_scid] = flow

        out_amt = int(forward["out_msat"])
        flow = ((0, 0), (1, out_amt))
        if out_scid in msat_moved:
            flow = msat_moved[out_scid]
            flow = (flow[0], (flow[1][0] + 1, flow[1][1] + out_amt))
        msat_moved[out_scid] = flow

        fees_collected_chanin = (fee, 0)
        if in_scid in channel_fees_collected:
            fees_collected_chanin = (channel_fees_collected[in_scid][0] + fee, channel_fees_collected[in_scid][1])
        channel_fees_collected[in_scid] = fees_collected_chanin

        fees_collected_chanout = (0, fee)
        if out_scid in channel_fees_collected:
            fees_collected_chanout = (channel_fees_collected[out_scid][0], channel_fees_collected[out_scid][1] + fee)
        channel_fees_collected[out_scid] = fees_collected_chanout

#report statistics for channels:
rows = []
total_moved = [[0, 0], [0, 0]]
total_net = 0
total_collected_fees = [0, 0]
total_rebalance_cost = [0, 0]
for scid in channels:
    collected_fees = channel_fees_collected[scid] if scid in channel_fees_collected else (0, 0)
    total_collected_fees = list(map(operator.add, tuple(total_collected_fees), collected_fees))
    moved = msat_moved[scid] if scid in msat_moved else ((0, 0), (0, 0))
    total_moved[0] = list(map(operator.add, tuple(total_moved[0]), moved[0]))
    total_moved[1] = list(map(operator.add, tuple(total_moved[1]), moved[1]))
    rebalance_cost = channel_rebalance_paid[scid] if scid in channel_rebalance_paid else (0, 0)
    total_rebalance_cost = list(map(operator.add, tuple(total_rebalance_cost), rebalance_cost))
#    net_earnings = ((collected_fees[0] + collected_fees[1]) - (rebalance_cost[0] + rebalance_cost[1]))
    net_earnings = collected_fees[1] - rebalance_cost[1]
    total_net = total_net + net_earnings
    channel_name = list(filter(lambda x: x["short_channel_id"] == scid, channel_aliases))
    print(channel_name)
    if (len(channel_name) > 0):
       channel_alias = channel_name[0]["node_alias"]
    else:
       channel_alias = scid
    rows.append((channel_alias, moved[0][0], moved[1][0], moved[0][1] / 1000000.0, moved[1][1] / 1000000.0, collected_fees[0] / 1000.0, collected_fees[1] / 1000.0, rebalance_cost[0] / 1000.0, rebalance_cost[1] / 1000.0, net_earnings / 1000.0))

print("────────────────┬───────────┬──────────────────────┬──────────────────────┬──────────────────────┬───────────┐")
print("   channel      │ # in, out │      ksat moved      │    fees collected    │  rebalancing costs   │    net    │")
print("════════════════╪═══════════╪══════════════════════╪══════════════════════╪══════════════════════╪═══════════╡")
for row in sorted(rows, key = lambda r: r[9]):
    print("%s │%4d, %4d │ %9.3f, %9.3f │ %9.3f, %9.3f │ %9.3f, %9.3f │ %9.3f │" % (row[0][:15].rjust(15), row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
print("════════════════╪═══════════╪══════════════════════╪══════════════════════╪══════════════════════╪═══════════╡")
print("           Total│%4d, %4d │ %4.3f BTC, %4.3f BTC │ %9.3f, %9.3f │ %9.3f, %9.3f │ %8.3f │" % (total_moved[0][0], total_moved[1][0], total_moved[0][1] / 100000000000.0, total_moved[1][1] / 100000000000.0, total_collected_fees[0] / 1000.0, total_collected_fees[1] / 1000.0, total_rebalance_cost[0] / 1000.0, total_rebalance_cost[1] / 1000.0, total_net / 1000.0))
print("────────────────┴───────────┴──────────────────────┴──────────────────────┴──────────────────────┴───────────┘")

