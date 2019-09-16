#!/bin/bash
#
# This shell script is used to create data to feed runeks' example python code at
# https://bitcoin.stackexchange.com/a/5241/89798 for signing against a basix tx
#
# For more info: https://github.com/Csi18nAlistairMann/bitcoin-sign-presegwit-tx
#
# I choose to reset regtest before every run.
# Sleeps added because I believe bitcoin is exiting the main thread and returning
# a value before children have finished cleaning up.
CURDIR=$(pwd)
cd $HOME/.bitcoin
bitcoin-cli -conf=$HOME/.bitcoin/regtest.conf -regtest stop
sleep 1
rm -rf $HOME/.bitcoin/regtest && bitcoind -conf=$HOME/.bitcoin/regtest.conf -regtest -daemon
sleep 2
bitcoin-cli -conf=$HOME/.bitcoin/regtest.conf -regtest generate 101 >/dev/null
cd $CURDIR
#
# We now have 50BTC available to us. Send 49.99 to another address so we are not
# moving a coinbase transaction, matching the original question
#
# Get the address we will later send the coins From
SEND_FROM_ADDRESS=$(bitcoin-cli -conf=$HOME/.bitcoin/regtest.conf getnewaddress)
#
# The wallet dumps out compressed private keys. We need the hex though, so get the
# compressed key first, and convert it afterwards
COMPRESSED_PRIV_KEY=$(bitcoin-cli -conf=$HOME/.bitcoin/regtest.conf dumpprivkey $SEND_FROM_ADDRESS)
HEX_PRIV_KEY=$(bitcoin-tool --input-type private-key-wif --input-format base58check --output-type all --output-format hex --network bitcoin-testnet --input $COMPRESSED_PRIV_KEY | grep "private-key.hex" | cut --delimiter=\: -f 2)
#
# Now send coins to the address we want to later send from
TXIN=$(bitcoin-cli -conf=$HOME/.bitcoin/regtest.conf sendtoaddress $SEND_FROM_ADDRESS 49.99)
#
# Now extract vout, known in runeks' code as OUTPUT_INDEX
VOUT=$(bitcoin-cli -conf=$HOME/.bitcoin/regtest.conf gettransaction $TXIN | grep vout | grep , | cut --delimiter=\: -f 2 | cut --delimiter=, -f 1 | cut --delimiter=\  -f 2)
#
# And the hex of the transaction
HEX_TRANSACTION=$(bitcoin-cli -conf=$HOME/.bitcoin/regtest.conf gettransaction $TXIN | grep hex | cut --delimiter=\" -f 4)
#
# Now get an address to which we can send the coins on
SEND_TO_ADDRESS=$(bitcoin-cli -conf=$HOME/.bitcoin/regtest.conf getnewaddress)
#
# And finally print what we've got in a cut and paste form ready to
# supercede what's in the example
echo 'HEX_TRANSACTION="'$HEX_TRANSACTION'"'
echo 'OUTPUT_INDEX='$VOUT
echo 'SEND_TO_ADDRESS="'$SEND_TO_ADDRESS'"'
echo 'PRIVATE_KEY=0x'$HEX_PRIV_KEY
