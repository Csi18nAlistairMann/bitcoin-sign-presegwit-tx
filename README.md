Alistair Mann - 16 Sep 2019

# Overview

This project was to learn more about how raw transactions can be signed, and
develops runeks' answer at https://bitcoin.stackexchange.com/a/5241/89798.
Please note ONLY presegwit transactions (version 01000000) are supported.

I expand on the original snippet to include generating the transactions used
and change the output to assist single-stepping through the resulting signed
transaction.

Linux, bash and python2 are assumed.

Note: This project was developed on a 2016-era Linux Mint 17.3 system
downloaded from https://linuxmint.com/edition.php?id=204. I'm aware that the
file brutus/ecdsa_ssl.py contains the line
`priv_key = ssl.BN_bin2bn(secret, 32, ssl.BN_new())` which segfaults on
Debian 9 (2017) and Kubuntu 18.04 (2018).

# Usage

To run with just the example regtest data:
`python2 scripts/bsec-3374.py`

To generate fresh data:
1. Install bitcoin-0.13.2
2. Add the provided `config/regtest.conf` file to your .bitcoin directory
3. Install bitcoin-tool (by Mat Anger)
4. Run `scripts/generate-new-tx.sh`
5. Edit the four displayed variables into `scripts/bsec-3374.py`
6. Run `python2 scripts/bsec-3374.py`

Optionally, to see your transaction single-stepped:
1. Install btcdeb
2. take the output from `bsec-3374.py` above and run as a command.
See `btcdeb/README.md` for more details.

# Repository contents
## bitcoin-0.13.2/
The code as originally written relied on uncompressed public keys being
used in constructing the transaction. As these required using a version
earlier than 0.6.0 - which seems pretty hard to find - I adjusted the
code to use the compressed public keys of later versions.

Also as the code stands segwit transactions cannot be signed. They
became the default with version 0.14.0.

I use version 0.13.2 to meet the above constraints, downloading it from:
https://bitcoin.org/bin/bitcoin-core-0.13.2/bitcoin-0.13.2.tar.gz and
provided here. Its SHA256 is
621201189c0409cb17a5073278872dcdcfff1ea147ead6958b55e94416b896d7

## config/regtest.conf
This project generates example presegwit transactions intended for the
regtest network. This is the config file used.

## bitcointools/
https://github.com/runeksvendsen/bitcointools as at 26 Sep 2012.
Runes K. Svendsen's tools, used for for serializing and deserializing
transactions, and base58 encoding/decoding. This is the nearest
equivalent I can find to Gavin Andresen's now defunct repository which
was used in the original answer.

## brutus/
https://github.com/runeksvendsen/brutus/ as at 30 Oct 2012.
Runes K. Svendsen's fork of ecdsa_ssl.py from Joric's Brutus
repository. Used for constructing public/private EC key pairs and ECDSA
signing.

## bitcoin-tool/
https://github.com/matja/bitcoin-tool as at 3 Mar 2018.
Mat Anger's tool, used to convert the compressed private keys to hex.

## scripts/
### scripts/generation-new-tx.sh
This script will reset regtest, then construct a single transaction on
your new regtest network. It will then display four variables:
HEX_TRANSACTION, OUTPUT_INDEX, SEND_TO_ADDRESS and PRIVATE_KEY.

This will give you insight into where ThePiachu's data came from.

### scripts/bsec-3374.py
This is an adaptation of runeks' script.

This script comes preloaded with regtest example data, not the mainnet
example data from ThePiachu's question. The original merely printed out
the raw, signed transaction; this one returns the btcdeb (see below)
command that allows for the transaction to be single-stepped, including
the original raw, signed transaction.

Call it with:
`python2 bsec-3374.py`

If the response is `Segmentation fault (core dumped)` you may be using
a system that's too new as per note at the top of this file. Sorry!
I don't have an answer as to what would correct it yet.

## btcdeb/
Not present in this repository but can be found at
https://github.com/kallewoof/btcdeb. This is Kallewoof's debugger that
allows single-stepping of BTC transactions. Directory contains a more
detailed description of use.

# Postscript
Do not use this code in a production environment or on a machine with
live keys! I have made no effort to check the safety of anyone's code
but my own.

Thank you to Runes K. Svendsen and Andrew Chow for direct help, thank
you to the others who created the code I've forked.
