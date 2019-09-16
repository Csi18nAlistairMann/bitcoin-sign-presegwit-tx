#!/usr/bin/env python
#
# Scan through coinbase transactions
# in the block database and report on
# how many blocks match a regex
#
from bsddb.db import *
from datetime import date
import logging
import os
import re
import sys

from BCDataStream import *
from block import scan_blocks
from collections import defaultdict
from deserialize import parse_Block
from util import determine_db_dir, create_env

def main():
  import optparse
  parser = optparse.OptionParser(usage="%prog [options]")
  parser.add_option("--datadir", dest="datadir", default=None,
                    help="Look for files here (defaults to bitcoin default)")
  parser.add_option("--regex", dest="lookfor", default="/P2SH/",
                    help="Look for string/regular expression (default: %default)")
  parser.add_option("--n", dest="howmany", default=999999, type="int",
                    help="Look back this many blocks (default: all)")
  parser.add_option("--start", dest="start", default=0, type="int",
                    help="Skip this many blocks to start (default: 0)")
  parser.add_option("--verbose", dest="verbose", default=False, action="store_true",
                    help="Print blocks that match")
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

  results = defaultdict(int)

  def count_matches(block_data):
    block_datastream.seek_file(block_data['nBlockPos'])
    data = parse_Block(block_datastream)
    coinbase = data['transactions'][0]
    scriptSig = coinbase['txIn'][0]['scriptSig']
    if results['skipped'] < options.start:
      results['skipped'] += 1
    else:
      results['checked'] += 1
      if re.search(options.lookfor, scriptSig) is not None:
        results['matched'] += 1
        if options.verbose: print("Block %d : %s"%(block_data['nHeight'], scriptSig.encode('string_escape')) )

    results['searched'] += 1
    return results['searched'] < options.howmany

  scan_blocks(db_dir, db_env, count_matches)

  db_env.close()

  percent = (100.0*results['matched'])/results['checked']
  print("Found %d matches in %d blocks (%.1f percent)"%(results['matched'], results['checked'], percent))

if __name__ == '__main__':
    main()
