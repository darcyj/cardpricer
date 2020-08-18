#!/usr/bin/env python3


# install stuff for using this in a conda env:
# make conda env, use pip to add asyncio and scrython
#  conda create --name scrython python=3.5 pip aiohttp
#  conda activate scrython
#  pip install asyncio
#  pip install scrython
#  pip install numpy
#  pip install pandas

import scrython      # for accessing scryfall api to get pricing data
import argparse      # so this script can be run from a shell
import numpy as np   # because i'm lost without vectorized boolean operations
import os.path       # to check if files exist (maybe not necessary...)
import pandas as pd  # for reading and writing csv files

# parse arguments
parser = argparse.ArgumentParser(description='cardpricer.py by JLD, August 2020')
parser._action_groups.pop()
required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')
required.add_argument('-i', '--input', action='store', required=True,
  help='input path to csv file (required)')
optional.add_argument('-o', '--output', action='store', required=False, default='overwrite',
  help='path for csv output. default overwrites input.')
args = parser.parse_args()

# handle output path
if args.output == "overwrite":
  out_fp = args.input
else:
  out_fp = args.output

# function for getting cheapest price
def get_cheapest(cardname):
  try:
    search = scrython.cards.Search(q='!' + '\"' + cardname + '\"', unique='prints')
    nc = search.total_cards()
    # get sets that the card appeared in
    sets=np.empty(nc, dtype='<U10')
    prices=np.empty(nc)
    for i in range(nc):
      # try to get set and price info.
      # if broken, price=nan so it gets removed later.
      try:
        sets[i] = search.data(i).get('set')
        prices[i] = search.data(i).get('prices').get('usd')
      except:
        sets[i] = 'err'
        prices[i] = np.nan
    # get prices for that card from each of those sets
    # get rid of sets and prices where price is nan
    sets = sets[np.isnan(prices) == False]
    prices = prices[np.isnan(prices) == False]
    # find min price
    min_ind = np.argmin(prices)
    out = {
      'cardname': cardname,
      'set': sets[min_ind],
      'price': prices[min_ind]
    }
  except:
    out = {
      'cardname': cardname,
      'set': 'error bad name',
      'price': np.nan
    }
  return(out)

# read in input csv
# check that file exists
print('Reading in your data...')
if os.path.exists(os.path.expanduser(args.input)):
  csvdata = pd.read_csv(args.input)
else:
  sys.exit("Error: input file not found. Try full path?")

# use list comprehension to get prices of each cardname
print('Checking prices... this may take a bit!')
ans = [get_cheapest(cn) for cn in csvdata.iloc[:,0]]

# cheat and use pandas to turn that dict into a DF and then
# combine it with the original csvdata to make output
rs = pd.DataFrame.from_dict(ans)
outputdata = pd.concat([csvdata, rs], axis=1)

print('writing output...')
outputdata.to_csv(out_fp, index=False)

print('...All done!')
