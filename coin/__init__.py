import databasing, networks, eccs, encodings, threads
from hashlib import sha256

db              = databasing.coinDB()
# miner           = mining.coinMiner()
network         = networks.coinNetwork()

ecc             = eccs.ellipticCurve()
hasher          = sha256
encoder         = encodings.b58encoder()
threader        = threads.coinThreader()


from os.path import isfile
if not isfile(db.dbFile):
    db.createDB()
