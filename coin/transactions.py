import coin
import coin.wallet

from hashlib import sha512
import json
from time import time
from os import urandom

VALIDATION_ADDITION_LENGTH = 20 #How do we determine this?
TRANSACTION_HASH_LENGTH = 32

def newTransaction(to, amount):

    outputs = coin.db.query("SELECT * from transactionOutputs LEFT JOIN transactionInputs where NOT EXISTS(SELECT * FROM transactionInputs where transactionOutputs.outputHash = transactionInputs.previousHash )", result="all") #Make a query to select outputs not used as inputs
    wallets = coin.db.query("SELECT * from wallets", result="all") #Make query to get all wallets

    for wallet in wallets:

        outputsUsed = []
        for output in outputs:

            if(output.address == wallet.address):

                myMoney += output.amount
                outputsUsed.append(output)

                if(myMoney>=amount):

                    newTransactionHash = urandom(TRANSACTION_HASH_LENGTH).encode('hex') #create a transaction hash

                    timestamp = str(time())

                    for usedOutputs in outputsUsed:

                        messageToSign = output.outputsHash + wallet.publicKey + timestamp

                        signature = coin.ecc.sign_message(int(wallet.privateKey),messageToSign)

                        correct = coin.ecc.verify_signature(coin.wallets.decompressPublicKey(publicKey),messageToSign,signature) #TODO: What is decompressPublicKey

                        assert correct == True

                        coin.db.doQuery("INSERT INTO transactions_inputs (previousOutput, publicKey, timestamp, signature, transactionHash) VALUES (?, ?, ?, ?, ?)", (output.outputHash, wallet.publicKey, timestamp, signature, newTransactionHash), result='none') #Query to create transaction inputs

                        #TODO: What is inputDict

                    newOutputHash = urandom(TRANSACTION_HASH_LENGTH).encode('hex')

                    coin.db.query("INSERT INTO transactionOutputs (amount, address, outputHash, transactionHash) VALUES (?, ?, ?, ?)",( str(amount), to, newOutputHash, newTransactionHash ), result="none") #Create transaction output to the receiver

                    #TODO: What is outputDict

                    if(myMoney > amount):

                        balance = myMoney - amount 

                        newOutputHash = urandom(TRANSACTION_HASH_LENGTH).encode('hex')

                        coin.db.doQuery("INSERT INTO transactions_outputs (amount, address, outputHash, transactionHash) VALUES (?, ?, ?, ?)",  (balance, wallet.myAddress, newOutputHash, newTransactionHash),  result='none') #Create a transaction to yourself for the remaining amount

                        #TODO: outputDict

                    coin.db.doQuery("INSERT INTO transactions (hash, timestamp) VALUES (?, ?)", (newTransactionHash, timestamp), result='none') #Enter the transaction details to transaction table

                    difficulty = 3
                    #TODO: Calculate difficulty according to the transaction amount?

                    createConfirmation(newTransactionHash,timestamp, difficulty) #Create confirmation(Proof of work)

                    transactionJSON = getJSONForTransaction(newTransactionHash)

                    coin.network.broadcastTransaction(transactionJSON)


def createConfirmation(transactionHash, timestamp, difficulty=3):

    diff = difficulty
    hasher = hashlib.sha512
    transactionValue = transactionHash + timestamp

    while true:

        addition = urandom(VALIDATION_ADDITION_LENGTH).encode('hex')
        confirmtionHash = coin.hasher(transactionValue + addition).hexdigest()

        if confirmtionHash[:diff].count("0") == difficulty:

            coin.network.broadcastConfirmation(transactionHash,difficulty,addition)    
            coin.db.doQuery('INSERT INTO confirmations (transactionHash, difficulty, addition, solution) VALUES (?, ?, ?, ?)', (transactionHash, difficulty, addition, solution), result='none') #Enter into confirmation table

            break


def getJSONForTransaction(transactionHash):

    transaction = coin.db.doQuery('SELECT hash,timestamp from transactions WHERE hash = ?', (transactionHash,), result='one')

    JSONdict = []
    JSONdict['inputs'] = []
    JSONdict['outputs'] = []

    JSONdict['transactionHash'] = transactionHash[0]
    JSONdict['timestamp'] = transaction[1]

    inputs = coin.db.doQuery("SELECT previousOutput, publicKey, timestamp, signature from transactions_inputs WHERE transactionHash = ?", (transactionHash,), result='all')
    for input in inputs:
        previousOutput,publicKey,timestamp,signature = input

        inputDict = {'previousOutput':previousOutput, 'publicKey':publicKey, 'timestamp':timestamp, 'signature':signature}
        JSONDict['inputs'].append(inputDict)

    outputs = coin.db.doQuery("SELECT amount, address, outputHash from transactions_outputs WHERE transactionHash = ?", (transactionHash,), result='all')
    for output in outputs:
        amount, address, outputHash = output

        outputDict = {'amount':str(amount), 'address':address, 'outputHash':outputHash}
        JSONDict['outputs'].append(outputDict)

    transactionJSON = json.dumps(JSONDict)
    return transactionJSON    


def addTransactionJSON(data):
    ''' Add a new transaction from JSON data '''
    
    transaction = json.loads(data)

    transactionHash = transaction['transactionHash']
    
    # check if transaction already exists
    db_transactions = coin.db.doQuery("SELECT hash from transactions where hash = ?", (transactionHash,), result='all')
    if(len(db_transactions) > 0):
        print "Transaction already exists"
        return False
    
    transactionTimestamp = transaction['timestamp']

    # timestamp must be sane
    current_time = time()
    if current_time < float(transactionTimestamp):
        print "Transaction timestamp is in the future"
        return False
    
    totalInputAmount = 0

    for oldInput in transaction['inputs']:
        outputHash = oldInput['previousOutput']

        # Input must have at least 2 confirmations
        numberOfConfirmations = coin.db.doQuery("SELECT count(*) FROM confirmations where transactionHash = ?",transactionHash, result='one')
        if(numberOfConfirmations<2):
            print "Less number of confirmations"
            return False
        
        # input must exist
        amount, address = coin.db.doQuery("SELECT amount, address from transactions_outputs WHERE outputHash = ?", (outputHash,), result='one')
        totalInputAmount += amount

        # Old input must not already exist in outputs
        check = coin.db.doQuery("SELECT count(*) FROM transactions_inputs WHERE outputHash = ?",outputHash, result='one')
        if(check!=0):
            print "error: transaction already used"
            return False

        publicKey = oldInput['publicKey']

        # validation todo: convert public key to address and check if address match for old output!



        # timestamp must be the same as transaction
        timestamp = oldInput['timestamp']
        if timestamp != transactionTimestamp:
            print "error3"
            return False

        signature = oldInput['signature']
        signature = signature.replace(' ','').replace('(','').replace(')','').split(',')
        signature = (long(signature[0]), long(signature[1]))
        
        # validate signature
        message = outputHash + publicKey + timestamp

        publicKey = coin.wallets.decompressPublicKey(publicKey)

        signature = coin.ecc.verify_signature(publicKey, message, signature)

        if not signature:
            print "error1"
            return False


    totalOutputAmount = 0

    for output in transaction['outputs']:
        
        transferAmount = output['amount']
        totalOutputAmount += int(transferAmount)

        toAddress = output['address']
        newOutputHash = output['outputHash']

    # amount must be valid
    if totalOutputAmount > totalInputAmount:
        print "error5"
        return False

    # if valid, add to db
    for oldInput in transaction['inputs']:
        outputHash = oldInput['previousOutput']
        publicKey = oldInput['publicKey']
        timestamp = oldInput['timestamp']
        signature = oldInput['signature']

        coin.db.doQuery("INSERT INTO transactions_inputs (previousOutput, publicKey, timestamp, signature, transactionHash) VALUES (?, ?, ?, ?, ?)", (outputHash, publicKey, timestamp, signature, transactionHash), result='none')

    for output in transaction['outputs']:
        transferAmount = output['amount']
        toAddress = output['address']
        newOutputHash = output['outputHash']

        coin.db.doQuery("INSERT INTO transactions_outputs (amount, address, outputHash, transactionHash) VALUES (?, ?, ?, ?)", (str(transferAmount), toAddress, newOutputHash, transactionHash), result='none')

    createTransactionConfirmation(transactionHash, transactionTimestamp)

    coin.db.doQuery("INSERT INTO transactions (hash, timestamp) VALUES (?, ?)", (transactionHash, transactionTimestamp), result='none')


def addConfirmationCSV(data):
    ''' Add confirmation from CSV '''

    transactionHash, difficulty, addition = data.split(",")
    difficulty = int(difficulty)

    if len(addition) != VALIDATION_ADDITION_LENGTH: # add some validation stuffz
        return

    maxDifficulty = coin.db.doQuery("select max(difficulty) from confirmations where transactionHash = ?", (transactionHash,), result='one')[0]
    
    if maxDifficulty >= difficulty:  #TODO: Why? What is maxDifficulty
        return
    
    timestamp = coin.db.doQuery("select timestamp from transactions where hash = ?", (str(transactionHash),), result='one')[0]

    if timestamp:

        transactionValue = transactionHash + timestamp
        solution = sha512(transactionValue + addition).hexdigest()

        if solution[:difficulty].count('0') == difficulty:

            coin.db.doQuery('DELETE FROM confirmations WHERE transactionHash = ?', (transactionHash, ), result='none') #TODO: Modify command instead of deleting and inserting
            
            coin.db.doQuery("INSERT INTO confirmations (transactionHash, difficulty, addition, solution) VALUES (?, ?, ?, ?)", (transactionHash, difficulty, addition, solution), result='none')