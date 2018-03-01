import coin
from time import sleep
from hashlib import sha512
from os import urandom

VALIDATION_ADDITION_LENGTH = 20


class coinMiner(object):
	""" Mining class for coin (creates confirmations) """

	def __init__(self):
		self.stopMiner = False

	def startMining(self):
		coin.threader.startBackgroundThread(self.runMiner)

	def runMiner(self):
		''' Start creating confirmations in the background '''

		while True:
			
			if self.stopMiner:
				break

			difficulty = coin.db.doQuery("select min(difficulty) from confirmations", result='one')[0]
			if not difficulty:
				sleep(1)
				continue
				
			transactionHash = coin.db.doQuery("select transactionHash from confirmations where difficulty = ? LIMIT 1", (str(difficulty),), result='one')[0]
			transactionTimestamp = coin.db.doQuery("select timestamp from transactions where hash = ?", (str(transactionHash),), result='one')[0]
	
			transactionValue = transactionHash + transactionTimestamp
			difficulty += 1
			
			while True:

				if self.stopMiner:
					break

				addition = urandom(VALIDATION_ADDITION_LENGTH).encode('hex')
				solution = sha512(transactionValue + addition).hexdigest()

				if solution.count('0') == difficulty:

					coin.db.doQuery('DELETE FROM confirmations WHERE transactionHash = ? AND difficulty = ?', (transactionHash, difficulty-1), result='none')
					coin.db.doQuery('INSERT INTO confirmations (transactionHash, difficulty, addition, solution) VALUES (?, ?, ?, ?)', (transactionHash, difficulty, addition, solution), result='none')
					
					coin.network.broadcastConfirmation(transactionHash, difficulty, addition)

					break

				sleep(0.1) # don't consume much resources


