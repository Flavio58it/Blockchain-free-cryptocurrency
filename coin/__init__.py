import databasing, networks, eccs, encodings, threads
from hashlib import sha256

db              = databasing.crackDB()
# miner           = mining.crackcoinMiner()
network         = networks.crackcoinNetwork()

ecc             = eccs
hasher          = sha256
encoder         = encodings.b58encoder()
threader        = threads.crackcoinThreader()


from os.path import isfile
if not isfile(db.dbFile):
    db.createDB()
