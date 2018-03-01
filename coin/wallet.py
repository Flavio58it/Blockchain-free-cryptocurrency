import coin
import hashlib

wallet_prefix="coin"

def compressPublicKey(publicKey):
    compressedKey=wallet_prefix
    
    #assign prime from ecc to p
    p = coin.ecc.p

    # x-coordinate of public key
    x = publicKey[0]
    # secp256k1 corresponds to curve y^2=x^3+7
    # So, y^2modp=(x^3+7)^((p+1)/4)modp
    # reference - https://bitcointalk.org/index.php?topic=644919.msg7205689#msg7205689
    y_squared=((x*x*x+7)%p)
    y_squared_square_root=pow(y_squared,(p+1)/4,p)
    # another root
    y2=y_squared_square_root*-1%p

    # we append p and m to identify which root to be chosen while decompressing
    if y2==publicKey[1]:
        compressedKey+='p'
    else:
        compressedKey+='m'

    a=hex(x)[2:].rstrip('L')
    if len(a)%2==1:
        a='0'+a
    a=a.decode('hex')

    compressedKey = coin.encoder.b58encode(a)
    return compressedKey


def decompressPublicKey(compressedKey):
    
    p = coin.ecc.p
    x = int(coin.encoder.b58decode(compressedKey[len(wallet_prefix)+1:]).encode('hex'), 16)

    y_squared=((x*x*x+7)%p)
    y_squared_square_root=pow(y_squared,(p+1)/4,p)

    if compressedKey[len(wallet_prefix)]=='p':
        # choose negative root
        y_squared_square_root=y_squared_square_root*-1%p

    return (x,y_squared_square_root)

def publicKeyToAddress(compressedKey):
    # produce address from compressed public key similar to bitcoin
    s = hashlib.new('sha256', compressedKey).digest()
    r = hashlib.new('ripemd160', s).digest()
    return wallet_prefix + coin.encoder.b58encode(r)

def CreateNewWallet():
    privateKey, PublicKey = coin.ecc.make_key()
    compressedKey = compressPublicKey(PublicKey)
    address = publicKeyToAddress(compressedKey)
    coin.db.doQuery('INSERT INTO wallets (privateKey, publicKey, address) VALUES (?, ?, ?)', (str(privateKey), str(compressedKey), address), result='none')

def printWalletInfo():
    outputs = coin.db.doQuery("select distinct transactions_outputs.amount, transactions_outputs.address, transactions_outputs.outputHash from transactions_outputs LEFT JOIN transactions_inputs WHERE NOT EXISTS(SELECT * FROM transactions_inputs WHERE transactions_outputs.outputHash = transactions_inputs.previousOutput)", result='all')
    wallets = coin.db.doQuery("select * from wallets", result='all')
    totalMoney = 0
    for wallet in wallets:
        ID, privateKey, publicKey, myAddress = wallet

        print "Wallet address: %s " % myAddress

	walletMoney = 0
	for output in outputs:
            amount, address, outputHash = output

            if address == myAddress:
                walletMoney += amount

        print "Money in wallet: %s\n" % str(walletMoney)
        totalMoney += walletMoney

    print "Total money: %s\n" % str(totalMoney)


