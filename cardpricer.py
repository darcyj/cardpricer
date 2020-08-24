#!/usr/bin/env python3


# install stuff for using this in a conda env:
# make conda env, use pip to add asyncio and scrython
#  conda create --name scrython python=3.5 pip aiohttp
#  conda activate scrython
#  pip install asyncio
#  pip install scrython
#  pip install pandas

import scrython      # for accessing scryfall api to get pricing data
import argparse      # so this script can be run from a shell
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
optional.add_argument('-b', '--basic', action='store', required=False, default=0.05,
  help='Price of basic lands. Prevents expensive queries to send to scryfall. Default=0.05')

args = parser.parse_args()

# handle output path
if args.output == "overwrite":
  out_fp = args.input
else:
  out_fp = args.output

# read in input csv
# check that file exists
print('Reading in your data...')
if os.path.exists(os.path.expanduser(args.input)):
  csvdata = pd.read_csv(args.input)
  csvdata = csvdata[csvdata.iloc[:,0].notna()]

else:
  sys.exit("Error: input file not found. Try full path?")

# build a huge "or" query for all the cards
# first add quotes and !s
def format_cname(cn):
  try:
    return('!"'+cn+'"')
  except:
    return("")

# function to sanitize names (alphanumeric and spaces)
def sanitize_name(cn):
  return(''.join(x for x in cn if x.isalpha() | (x==' ')).lower())

# scryfall api will only do 18 "or" cards at a time. So I'm doing 15 at a 
# time to be safe. 
cnames_formatted = [format_cname(cn) for cn in csvdata.iloc[:,0]]
# remove basic lands
bls = ['island','swamp','forest','plains','mountain']
bland_inds = [i for i,x in enumerate(cnames_formatted) if sanitize_name(x) in bls]
for i in sorted(bland_inds, reverse=True):
	del cnames_formatted[i]

# now concatenate with ' or ' between them. I hate this syntax but whatever.
n = 15
cnames_binned = [cnames_formatted[i * n:(i + 1) * n] for i in range((len(cnames_formatted) + n - 1) // n )]  
qrys_binned = [' or '.join(cb) for cb in cnames_binned]

# define function that will extract take a qry from qrys_binned, get results, and pull out info.
# hard part is that returned info is paginated, hence the while loop (no way to know npages...)
def mine_qry(qry):
  stuff = []
  morepages = True
  currentpage = 1 # yes, it starts at 1
  while morepages:
    rslt = scrython.cards.Search(q=qry, unique='prints', page=currentpage)
    # pull relevant info out of rslt and put it into cnames, sets, usd.
    for i in range(rslt.data_length()):
      try:
        stuff.append(dict({
          'name': rslt.data(i).get('name'),
          'set': rslt.data(i).get('set'),
          'usd': rslt.data(i).get('prices').get('usd')
        }))
      except:
        stuff.append(dict({
          'name': 'error',
          'set': 'error',
          'usd': None
        })) 
    morepages = rslt.has_more()
    currentpage += 1
  return(stuff)

# use a damn for loop to go nuts with mine_qry and mine all the queries.
# this way I can output "processed query 1 / 12" or whatever
print('processing query chunks...')
results = []
nq = len(qrys_binned)
for i in range(nq):
  results += mine_qry(qrys_binned[i])
  print("  chunk " + str(i+1) + "/" + str(nq) + " done")

# add basic lands back into results
basicprice = args.basic # this is for lazy debugging...
results += [{'name': 'Plains',   'set': 'xxx', 'usd': basicprice}]
results += [{'name': 'Island',   'set': 'xxx', 'usd': basicprice}]
results += [{'name': 'Swamp',    'set': 'xxx', 'usd': basicprice}]
results += [{'name': 'Mountain', 'set': 'xxx', 'usd': basicprice}]
results += [{'name': 'Forest',   'set': 'xxx', 'usd': basicprice}]

# cheat and use pandas to turn that dict into a DF 
results_df = pd.DataFrame.from_dict(results)
# drop rows from results_df where price is None or nan or whatever
results_df = results_df.dropna()
results_df = results_df.reset_index(drop=True)
# create column of sanitized names. a-z 0-9 only, all lower case
results_df['san_name'] = [sanitize_name(cn) for cn in results_df['name']]

# quick which_min function so i don't need numpy anymore
# gives index of first instance of minimum value
def which_min(x):
  x2 = [float(q) for q in x]
  mx = min(x2)
  for i in range(len(x2)):
    if(x2[i] == mx):
      return(i)

# for each cardname in csvdata col 0, get best price and set.
# where name is not found in there, use startswith.
def get_cheapest(cn):
  # make sure cn is actually in results_df. 
  num_in = sum(results_df['san_name'] == sanitize_name(cn))
  cn_proxy = '12345@@@ERROR' # something that a magic card can't be named
  if num_in >= 1:
    cn_proxy = cn
  else:
    # try to find out if we can used sw=startswith to pull out the card.
    sw = [nm.startswith(sanitize_name(cn)) for nm in results_df['san_name']]
    if sum(sw) >= 1:
      # check that all matches (where sw==True) are identical
      sw_names = []
      for i in range(len(sw)):
        if sw[i]:
          sw_names.append(results_df['name'][i])
      if len(set(sw_names)) <= 1:
        cn_proxy = sw_names[0]
  if(cn_proxy != '12345@@@ERROR'):
    try:
      # if a cn_proxy was actually found, return stuff
      rows2get = results_df['san_name'] == sanitize_name(cn_proxy)
      df_cn = results_df[rows2get]
      df_cn = df_cn.reset_index(drop=True)
      wm = which_min(df_cn['usd'])
      return({
        'name': cn,
        'matchname': df_cn['name'][wm],
        'set': df_cn['set'][wm],
        'usd': df_cn['usd'][wm],
      })
    except:
      # woops it didn't work, return fail
      return({
        'name': cn,
        'matchname': 'error',
        'set': 'error',
        'usd': None,
      })
  else:
    # if not, return error object so user knows which cards are misspelled
    return({
      'name': cn,
      'matchname': 'no match',
      'set': 'no match',
      'usd': None,
    })

# use list comprehension to build output list of dicts
print('Finding cheapest printings...')
cheapo_results = [get_cheapest(cn) for cn in csvdata.iloc[:,0]]

# go through cheapo_results and notify user of imperfect matches
print('Checking for warnings...')
nwarns = 0
for cr in cheapo_results:
  if sanitize_name(cr.get('name')) != sanitize_name(cr.get('matchname')):
    print('  Warning: "' + cr.get('name') + '" matched to "' + cr.get('matchname') + '"')
    nwarns += 1

print('  (Found ' + str(nwarns) + ' warnings)')


# cheat and use pandas to turn that dict into a DF and then
# combine it with the original csvdata to make output
rs = pd.DataFrame.from_dict(cheapo_results)

# check for catastrophic sorting error (should be impossible...)
if all(rs['name'] == csvdata.iloc[:,0]):
  outputdata = pd.concat([csvdata, rs], axis=1)
  print('writing output...')
  outputdata.to_csv(out_fp, index=False)
  print('All done!')
else:
  sys.exit("ERROR: catastrophic sorting failure. Not sure what went wrong.")


