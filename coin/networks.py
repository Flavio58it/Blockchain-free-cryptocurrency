import coin
import coin.transactions
import socket

import zlib


NETWORK_PORT = 31338

LOOP_TIMEOUT = 4
NETWORK_SERVER_TIMEOUT = 4

# packet names definitions
packet_prefix = "coin"

# packet prefixes
packet_sync_request = packet_prefix + "sync"
packet_payment_new = packet_prefix + "paynew"
packet_payment_confirmation_request = packet_prefix + "payrconf" # request payment confirmations
packet_payment_confirmation = packet_prefix + "payconfirm" # new confirmation


def hasPacketPrefix(data, packetPrefix):
    ''' Check if packet starts with some type prefix '''

    l = len(packetPrefix)
    if len(data) >= l:
        return data[:l] == packetPrefix

    return False


class coinNetwork(object):

    def __init__(self):
        self.stopServer = False
        self.localIP = self.getLocalIP()

    def startNetworking(self):
        ''' Start main threads for networking '''

        coin.threader.startBackgroundThread(self.runServer)

    def sendToNode(self, ip, msg):
        ''' Send UDP Packet to node '''

        sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sendSocket.sendto(msg, (ip, NETWORK_PORT))

    def handleServerInput(self, data, ip):


        # reply to broadcast packets
        if hasPacketPrefix(data, packet_sync_request):
            # todo: do proper sync, not send everything
            transactions = coin.db.doQuery("SELECT hash from transactions WHERE hash != 'd34db33f'", result='all') # everything except genesis transaction
            if len(transactions) != 0 :
                for transaction in transactions:
                    transactionHash = transaction[0]

                    # send transaction
                    transactionJSON = coin.transactions.getJSONForTransaction(transactionHash)
                    coin.network.sendToNode(ip, packet_payment_new + zlib.compress(transactionJSON) )
                
                    # send current confirmation
                    difficulty,addition = coin.db.doQuery("select difficulty,addition from confirmations where transactionHash = ?", (transactionHash,), result='one')
                    data = "%s,%s,%s" % (transactionHash,str(difficulty),addition)
                    coin.network.sendToNode(ip, packet_payment_confirmation + data)


        if hasPacketPrefix(data, packet_payment_new):
            coin.transactions.addTransactionJSON( zlib.decompress(data[len(packet_payment_new):]) )

        if hasPacketPrefix(data, packet_payment_confirmation):
            coin.transactions.addConfirmationCSV(data[len(packet_payment_confirmation):])
            

    def runServer(self):

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET , socket.SO_REUSEADDR , 1)
        self.serverSocket.bind(("", NETWORK_PORT))  # listen on all interfaces
        self.serverSocket.settimeout(LOOP_TIMEOUT)

        while True:

            if self.stopServer:
                self.serverSocket.close()
                break

            try:
                data, addr = self.serverSocket.recvfrom(4096)
            except:
                continue

            ip = addr[0]
            if ip == self.localIP or ip == "127.0.0.1":
                continue

            if hasPacketPrefix(data, packet_prefix):
                self.handleServerInput(data, ip)

    def getLocalIP(self):
        ''' Fetches local IP for primary interface '''

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("iris.nitk.ac.in",80))
        ip = s.getsockname()[0]
        s.close()

        return ip

    def broadcastSync(self):
        ''' Send network sync broadcast '''

        self.broadcastPacket(packet_sync_request)

    def broadcastConfirmation(self, transactionHash, difficulty, addition):
        ''' Send transaction confirmation broadcast '''

        data = "%s,%s,%s" % (transactionHash,str(difficulty),addition)
        self.broadcastPacket(packet_payment_confirmation + data)

    def broadcastTransaction(self, transactionJSON):
        ''' Send transaction broadcast '''

        self.broadcastPacket(packet_payment_new + zlib.compress(transactionJSON) )

    def broadcastPacket(self, packet):
        ''' Broadcast packet to local network '''

        broadcastSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcastSocket.sendto(packet, ('255.255.255.255', NETWORK_PORT))
