# Part of my research into signing raw, presegwit transactions at
# https://github.com/Csi18nAlistairMann/bitcoin-sign-presegwit-tx
#
# Based on runek's answer at https://bitcoin.stackexchange.com/a/5241/89798
import sys
sys.path.append('../bitcointools/')
sys.path.append('../brutus/')
#bitcointools
from deserialize import parse_Transaction, opcodes
from BCDataStream import BCDataStream
from base58 import bc_address_to_hash_160, b58decode, public_key_to_bc_address, hash_160_to_bc_address

import ecdsa_ssl

import Crypto.Hash.SHA256 as sha256
import Crypto.Random

# Regtest/testnet transaction, from which we want to redeem an output
HEX_TRANSACTION="0100000001610fd505b322250f42ba0f05558bae634f8d509a98b270b7eae1282b6b620b9e000000004847304402206bc62564268f737ef8492eb9854e3500b6ec21d8244e4b0f72f153c1499849fb0220500c8ad92fbd77c4360162aee47568ea79db66131ea3ba6c0c12e7d13aa156fc01feffffff0240330f00000000001976a91400a3b51725584541ecdd5156bb78b349a838d60988acc0aff629010000001976a914e541bd2f000e84bfe057c30a5af56d033a6b4aa988ac50000000"
#output to redeem. must exist in HEX_TRANSACTION
OUTPUT_INDEX=1
# Regtest/testnet address we want to send the redeemed coins to.
#REPLACE WITH YOUR OWN ADDRESS, unless you're feeling generous
SEND_TO_ADDRESS="mwV13ymMffD6XXVQeuvHPSR4CkEYMvPSxt"
#fee we want to pay (in BTC)
TX_FEE=0.001
#constant that defines the number of Satoshis per BTC
COIN=100000000
#constant used to determine which part of the transaction is hashed.
SIGHASH_ALL=1
#private key whose public key hashes to the hash contained in scriptPubKey of output number *OUTPUT_INDEX* in the transaction described in HEX_TRANSACTION
PRIVATE_KEY=0x1a355c7187e58c91ef40abee31dcf33bd36993756b853674cfc2156b4d2b9a13

def dsha256(data):
   return sha256.new(sha256.new(data).digest()).digest()

tx_data=HEX_TRANSACTION.decode('hex_codec')
tx_hash=dsha256(tx_data)

#here we use bitcointools to parse a transaction. this gives easy access to the various fields of the transaction from which we want to redeem an output
stream = BCDataStream()
stream.write(tx_data)
tx_info = parse_Transaction(stream)

if len(tx_info['txOut']) < (OUTPUT_INDEX+1):
   raise RuntimeError, "there are only %d output(s) in the transaction you're trying to redeem from. you want to redeem output index %d" % (len(tx_info['txOut']), OUTPUT_INDEX)

#this dictionary is used to store the values of the various transaction fields
#  this is useful because we need to construct one transaction to hash and sign
#  and another that will be the final transaction
tx_fields = {}

##here we start creating the transaction that we hash and sign
sign_tx = BCDataStream()
##first we write the version number, which is 1
tx_fields['version'] = 1
sign_tx.write_int32(tx_fields['version'])
##then we write the number of transaction inputs, which is one
tx_fields['num_txin'] = 1
sign_tx.write_compact_size(tx_fields['num_txin'])

##then we write the actual transaction data
#'prevout_hash'
tx_fields['prevout_hash'] = tx_hash
sign_tx.write(tx_fields['prevout_hash']) #hash of the the transaction from which we want to redeem an output
#'prevout_n'
tx_fields['output_index'] = OUTPUT_INDEX
sign_tx.write_uint32(tx_fields['output_index']) #which output of the transaction with tx id 'prevout_hash' do we want to redeem?

##next comes the part of the transaction input. here we place the script of the *output* that we want to redeem
tx_fields['scriptSigHash'] = tx_info['txOut'][OUTPUT_INDEX]['scriptPubKey']
#first write the size
sign_tx.write_compact_size(len(tx_fields['scriptSigHash']))
#then the data
sign_tx.write(tx_fields['scriptSigHash'])

#'sequence'
tx_fields['sequence'] = 0xffffffff
sign_tx.write_uint32(tx_fields['sequence'])

##then we write the number of transaction outputs. we'll just use a single output in this example
tx_fields['num_txout'] = 1
sign_tx.write_compact_size(tx_fields['num_txout'])
##then we write the actual transaction output data
#we'll redeem everything from the original output minus TX_FEE
tx_fields['value'] = tx_info['txOut'][OUTPUT_INDEX]['value']-(TX_FEE*COIN)
sign_tx.write_int64(tx_fields['value'])
##this is where our scriptPubKey goes (a script that pays out to an address)
#we want the following script:
#"OP_DUP OP_HASH160  OP_EQUALVERIFY OP_CHECKSIG"
address_hash = bc_address_to_hash_160(SEND_TO_ADDRESS)
#chr(20) is the length of the address_hash (20 bytes or 160 bits)
scriptPubKey = chr(opcodes.OP_DUP) + chr(opcodes.OP_HASH160) + \
   chr(20) + address_hash + chr(opcodes.OP_EQUALVERIFY) + chr(opcodes.OP_CHECKSIG)
#first write the length of this lump of data
tx_fields['scriptPubKey'] = scriptPubKey
sign_tx.write_compact_size(len(tx_fields['scriptPubKey']))
#then the data
sign_tx.write(tx_fields['scriptPubKey'])

#write locktime (0)
tx_fields['locktime'] = 0
sign_tx.write_uint32(tx_fields['locktime'])
#and hash code type (1)
tx_fields['hash_type'] = SIGHASH_ALL
sign_tx.write_int32(tx_fields['hash_type'])

#then we obtain the hash of the signature-less transaction (the hash that we sign using our private key)
hash_scriptless = dsha256(sign_tx.input)

##now we begin with the ECDSA stuff.
## we create a private key from the provided private key data, and sign hash_scriptless with it
## we also check that the private key's corresponding public key can actually redeem the specified output
## Note that we must now force use of key compression to match bitcoin-0.6.0 and later

k = ecdsa_ssl.KEY()
k.generate(('%064x' % PRIVATE_KEY).decode('hex'))
k.set_compressed(True)

#here we retrieve the public key data generated from the supplied private key
pubkey_data = k.get_pubkey()
#then we create a signature over the hash of the signature-less transaction
sig_data=k.sign(hash_scriptless)
#a one byte "hash type" is appended to the end of the signature (https://en.bitcoin.it/wiki/OP_CHECKSIG)
sig_data = sig_data + chr(SIGHASH_ALL)

#let's check that the provided private key can actually redeem the output in question
if (bc_address_to_hash_160(public_key_to_bc_address(pubkey_data)) != tx_info['txOut'][OUTPUT_INDEX]['scriptPubKey'][3:-2]):
   bytes = b58decode(SEND_TO_ADDRESS, 25)
   raise RuntimeError, "The supplied private key cannot be used to redeem output index %d\nYou need to supply the private key for address %s" % \
                           (OUTPUT_INDEX, hash_160_to_bc_address(tx_info['txOut'][OUTPUT_INDEX]['scriptPubKey'][3:-2], bytes[0]))

##now we begin creating the final transaction. this is a duplicate of the signature-less transaction,
## with the scriptSig filled out with a script that pushes the signature plus one-byte hash code type, and public key from above, to the stack

final_tx = BCDataStream()
final_tx.write_int32(tx_fields['version'])
final_tx.write_compact_size(tx_fields['num_txin'])
final_tx.write(tx_fields['prevout_hash'])
final_tx.write_uint32(tx_fields['output_index'])

##now we need to write the actual scriptSig.
## this consists of the DER-encoded values r and s from the signature, a one-byte hash code type, and the public key in uncompressed format
## we also need to prepend the length of these two data pieces (encoded as a single byte
## containing the length), before each data piece. this length is a script opcode that tells the
## Bitcoin script interpreter to push the x following bytes onto the stack

scriptSig = chr(len(sig_data)) + sig_data + chr(len(pubkey_data)) + pubkey_data
#first write the length of this data
final_tx.write_compact_size(len(scriptSig))
#then the data
final_tx.write(scriptSig)

##and then we simply write the same data after the scriptSig that is in the signature-less transaction,
#  leaving out the four-byte hash code type (as this is encoded in the single byte following the signature data)

final_tx.write_uint32(tx_fields['sequence'])
final_tx.write_compact_size(tx_fields['num_txout'])
final_tx.write_int64(tx_fields['value'])
final_tx.write_compact_size(len(tx_fields['scriptPubKey']))
final_tx.write(tx_fields['scriptPubKey'])
final_tx.write_uint32(tx_fields['locktime'])

#prints out the final transaction in hex format (can be used as an argument to bitcoind's sendrawtransaction)
# print final_tx.input.encode('hex')

# print out what we have suitable for running as a btcdeb command
print 'btcdeb --txin ' + HEX_TRANSACTION + ' --tx ' + final_tx.input.encode('hex')
