import coin.wallet
import coin.transactions
import sqlite3
import threading


COIN_DB_TEMPLATE = 'coinBase.sql'
COIN_DB_FILE = 'coin.db'


class crackDB(object):
	""" coin database class """

	def __init__(self, dbFile = COIN_DB_FILE):
		
		self.dbFile = dbFile
		self.dblock = threading.Lock()

	def doQuery(self, query, args=False, result='all'):
		''' Perform a thread-safe query on the database '''

		self.dblock.acquire()

		self.conn = sqlite3.connect(self.dbFile)
		self.cursor = self.conn.cursor()

		if args:
			self.cursor.execute(query, args)
		else:
			self.cursor.execute(query)

		res = ''
		if result == 'all':
			res = coin.db.cursor.fetchall()
		if result == 'one':
			res = coin.db.cursor.fetchone()

		self.conn.commit()
		self.conn.close()

		self.dblock.release()

		return res


	def createDB(self):
		''' Create database from template and create wallet '''

		sql = open(COIN_DB_TEMPLATE,'r').read() 
		tmpConn = sqlite3.connect(self.dbFile)
		tmpCursor = tmpConn.cursor()
		tmpCursor.executescript(sql)
		tmpConn.commit()
		tmpConn.close()

		coin.wallet.CreateNewWallet()
