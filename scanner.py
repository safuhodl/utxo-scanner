#!/usr/bin/env python3

import base64
import json
import argparse
import configparser
from sys import stdin, stdout
from urllib.request import build_opener

# user-specific params
configparser = configparser.ConfigParser()
configparser.read('scanner.conf')
config = configparser['BITCOINRPC']
rpc_user = config['username']
rpc_password = config['password']
rpc_host = config['host']
rpc_port = int(config['port'])

auth = base64.encodebytes('{}:{}'.format(rpc_user, rpc_password).encode()).decode().replace('\n', '')
url = "http://{}:{}".format(rpc_host, rpc_port)
def rpc_request(method, *params):
    opener = build_opener()
    opener.addheaders = [("Authorization", "Basic %s" % auth)]
    data = { "jsonrpc": "1.0", "id":"", "method":method, "params": list(params) }
    resp = opener.open(url, json.dumps(data).encode('utf-8')).read().strip().decode('utf-8')
    return json.loads(resp)['result']

def to_sat(value):
    return int(value * 100000000)

def find_outs(addresses, start_height, end_height, progress_hook=None):
    # script_types = ['pubkeyhash', 'scripthash', 'witness_v0_keyhash', 'witness_v0_scripthash']
    outs = { address : [] for address in addresses }
    best_block_hash = rpc_request('getbestblockhash')
    best_block_height = rpc_request('getblockheader', best_block_hash)['height']
    end_height = min(end_height, best_block_height)
    for i,height in enumerate(range(start_height, end_height+1)):
        block_hash = rpc_request('getblockhash', height)
        block = rpc_request('getblock', block_hash,  2)
        if progress_hook:
            progress_hook(i, end_height - start_height, 'Fetching blocks')
        for tx in block['tx']:
            for out in tx['vout']:
                scriptpubkey = out['scriptPubKey']
                # if scriptpubkey['type'] not in scriptpubkey_types:
                #     continue
                out_address = scriptpubkey.get('address')
                if out_address in outs:
                    outs[out_address].append((tx['txid'], out['n'], to_sat(out['value'])))
    return outs

def filter_spent(outs):
    unspent_outs = { address: [] for address in outs.keys() }
    for address in outs.keys():
        for out in outs[address]:
            out_info = rpc_request('gettxout', out[0], out[1])
            if out_info is not None and address == out_info['scriptPubKey']['address']:
                unspent_outs[address].append(out)
    return unspent_outs

def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    stdout.flush()

def main():
    parser = argparse.ArgumentParser('Find unspent outputs for addresses')
    parser.add_argument('start_height', metavar='START-HEIGHT', type=int,
                        help='the block height from which to start scanning')
    parser.add_argument('-n', '--nblocks', metavar='NBLOCKS', type=int, default=144,
                        help='the number of blocks to scan')
    parser.add_argument('-f', '--format', default='utxo', choices=['utxo', 'address', 'balance'],
                        help='the format of the output')
    parser.add_argument('-p', '--progress', action='store_true',
                        help='display scanning progress')
    args = parser.parse_args()

    if args.start_height < 0 or args.nblocks < 1:
        raise Exception('Invalid block height arguments')

    input = []
    while True:
        line = stdin.readline().strip()
        if line == '':
            break
        input.append(line)
    outs = find_outs(input, args.start_height, args.start_height + args.nblocks, progress if args.progress else None)
    unspent_outs = filter_spent(outs)
    print()

    if args.format == 'utxo':
        print(unspent_outs)
    elif args.format == 'address':
        for address in unspent_outs.keys():
            addr_balance = sum([o[2] for o in unspent_outs[address]])
            print('{},{}'.format(address,addr_balance))
    elif args.format == 'balance':
        balance = 0
        for address in unspent_outs.keys():
            balance += sum([o[2] for o in unspent_outs[address]])
        print(balance)

if __name__ == '__main__':
    main()

