#!/usr/bin/python

import coin

import coin.wallet
import coin.transactions

#while 1:
privateKey, publicKey = coin.ecc.make_key()
compressedPublicKey = coin.wallet.compressPublicKey(publicKey)
newAddress = coin.wallet.publicKeyToAddress(compressedPublicKey)

#print newAddress[:9]
#if newAddress[:9] in coolAddressNames:
print "Private key:\n\t%s" % privateKey
#print publicKey
print "Compressed public key:\n\t%s" % compressedPublicKey
print "Address:\n\t%s" % newAddress
