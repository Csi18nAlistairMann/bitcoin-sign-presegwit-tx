#!/usr/bin/env python
#
# Scan through coinbase transactions
# in the block database intepreting
# bytes 0-3 (and 1-4 if byte 0 is 0x04)
# as a block height, looking for plausible
# future heights.
#
from bsddb.db import *
from datetime import date, datetime
import logging
import os
import re
import sys

from BCDataStream import *
from block import scan_blocks
from collections import defaultdict
from deserialize import parse_Block
from util import determine_db_dir, create_env

def approx_date(height):
  timestamp = 1231006505+height*10*60
  t = datetime.fromtimestamp(timestamp)
  return "%d-%.2d"%(t.year, t.month)

def main():
  import optparse
  parser = optparse.OptionParser(usage="%prog [options]")
  parser.add_option("--datadir", dest="datadir", default=None,
                    help="Look for files here (defaults to bitcoin default)")
  (options, args) = parser.parse_args()

  if options.datadir is None:
    db_dir = determine_db_dir()
  else:
    db_dir = options.datadir

  try:
    db_env = create_env(db_dir)
  except DBNoSuchFileError:
    logging.error("Couldn't open " + db_dir)
    sys.exit(1)

  blockfile = open(os.path.join(db_dir, "blk%04d.dat"%(1,)), "rb")
  block_datastream = BCDataStream()
  block_datastream.map_file(blockfile, 0)

  def gather(block_data):
    block_datastream.seek_file(block_data['nBlockPos'])
    data = parse_Block(block_datastream)
    height = block_data['nHeight']
    coinbase = data['transactions'][0]
    scriptSig = coinbase['txIn'][0]['scriptSig']
    if len(scriptSig) < 4:
      return True
    (n,) = struct.unpack_from('<I', scriptSig[0:4])
    if n < 6*24*365.25*100:  # 200 years of blocks:
      print("%d: %d (%s) version: %d/%d"%(height, n, approx_date(n), block_data['b_version'],coinbase['version']))

    if ord(scriptSig[0]) == 0x03:
      (n,) = struct.unpack_from('<I', scriptSig[1:4]+'\0')
      if n < 6*24*365.25*100:  # 200 years of blocks:
        print("%d: PUSH %d (%s) version: %d/%d"%(height, n, approx_date(n), block_data['b_version'],coinbase['version']))

    return True

  scan_blocks(db_dir, db_env, gather)

  db_env.close()

if __name__ == '__main__':
    main()
