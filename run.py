#!/usr/bin/python

import coin

import coin.wallet
import coin.transactions
import traceback


commands = {'q':'quit', 'h':'help', 'b':'broadcast', 't':'transaction', 'i':'information'}
running = True

if __name__ == "__main__":

    coin.network.startNetworking()
    # coin.miner.startMining()
    
    while running:

        try:

            ui = raw_input("> ")

            if ui == 'q':
                break

            if ui == 'h':
                for c in commands:
                    print "%s: %s" % (c, commands[c])

            if ui == 't':
                to = raw_input("To: ")
                amount = raw_input("Amount: ")
                coin.transactions.newTransaction(to, amount)

            if ui == 'i':
                coin.wallet.printWalletInfo()

            if ui == 'b':
                coin.network.broadcastSync()

        except KeyboardInterrupt:
            print "Exiting ..."
            running = False
            break

        except Exception as e:
            print "Exception in main: " + e.message
            print traceback.format_exc()
            break

    coin.network.stopServer = True
    # coin.miner.stopMiner = True
    coin.threader.waitForThreads()
