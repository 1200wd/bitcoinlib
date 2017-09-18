

# TODO: cleanup


#
# === TRANSACTIONS AND BITCOIND EXAMPLES
#

from bitcoinlib.services.bitcoind import BitcoindClient

bdc = BitcoindClient.from_config()

# Deserialize and verify a transaction
txid = '73652b5f704b0a112b8bc68d063dac6238eb3e2861074a7a12ce24e2a332bd45'
rt = bdc.getrawtransaction(txid)
print("Raw: %s" % rt)
t = Transaction.import_raw(rt)
pprint(t.dict())
print("Verified: %s" % t.verify())

# Deserialize transactions in latest block with bitcoind client
MAX_TRANSACTIONS_VIEW = 100
error_count = 0
if MAX_TRANSACTIONS_VIEW:
    print("\n=== DESERIALIZE LAST BLOCKS TRANSACTIONS ===")
    blockhash = bdc.proxy.getbestblockhash()
    bestblock = bdc.proxy.getblock(blockhash)
    print('... %d transactions found' % len(bestblock['tx']))
    ci = 0
    ct = len(bestblock['tx'])
    for txid in bestblock['tx']:
        ci += 1
        print("\n[%d/%d] Deserialize txid %s" % (ci, ct, txid))
        rt = bdc.getrawtransaction(txid)
        print("Raw: %s" % rt)
        t = Transaction.import_raw(rt)
        pprint(t.dict())
        print("Verified: %s" % t.verify())
        if ci > MAX_TRANSACTIONS_VIEW:
            break
    print("===   %d raw transactions deserialised   ===" %
          (ct if ct < MAX_TRANSACTIONS_VIEW else MAX_TRANSACTIONS_VIEW))
    print("===   errorcount %d" % error_count)
    print("===   D O N E   ===")

    # Deserialize transactions in the bitcoind mempool client
    print("\n=== DESERIALIZE MEMPOOL TRANSACTIONS ===")
    newtxs = bdc.proxy.getrawmempool()
    ci = 0
    ct = len(newtxs)
    print("Found %d transactions in mempool" % len(newtxs))
    for txid in newtxs:
        ci += 1
        print("[%d/%d] Deserialize txid %s" % (ci, ct, txid))
        try:
            rt = bdc.getrawtransaction(txid)
            print("- raw %s" % rt)
            t = Transaction.import_raw(rt)
            pprint(t.dict())
        except Exception as e:
            print("Error when importing raw transaction %d, error %s", (txid, e))
            error_count += 1
        if ci > MAX_TRANSACTIONS_VIEW:
            break
    print("===   %d mempool transactions deserialised   ===" %
          (ct if ct < MAX_TRANSACTIONS_VIEW else MAX_TRANSACTIONS_VIEW))
    print("===   errorcount %d" % error_count)
    print("===   D O N E   ===")
