# cardpricer
Python program to fetch cheapest prices for a csv full of magic cards

## What does this thing do?
cardpricer.py takes a csv full of magic cards, and finds the *printing* of each card that has the lowest scryfall price datum. For example, the price of Goblin Guide's cheapest printing. Well it's not going to be the grand prix promo which costs like $25 - it will be the double master's edition that goes for $5. So you'll get $5 as the output price and 2XM as the set code. Where do scryfall prices come from? they come from reputable magic card sellers like tcgplayer. https://scryfall.com/docs/faqs/where-do-scryfall-prices-come-from-7. Anyway I wrote this as an alternative to using deckstats.net because that damn website told me that terramorphic expanse costs $4 when the cheapest printing should have been $0.20 or something. 

## Installation instructions (linux, and maybe mac?)

1. make sure you have `conda` installed. skip this if you already have conda. you could also skip this step and just install all the requirements using `pip`, but that would be messy. I prefer miniconda. https://docs.conda.io/projects/conda/en/latest/user-guide/install/. I'm not 100% sure about this but I think you need to add channels `defaults` and `conda-forge`. Do that with `conda config --add channels defaults conda-forge`.

2. use conda to make an environment for scrython, which is a python library that allows us to use scryfall.com's api. 
```
conda create --name scrython python=3.5 pip aiohttp
conda activate scrython
pip install asyncio
pip install scrython
pip install pandas
conda deactivate scrython
```

3. download this git repository somewhere convenient. maybe downloads? If you don't have `git`installed, either install it, or just download the repo manually (i don't even know how lol don't ask me)
```
git clone https://github.com/darcyj/cardpricer ~/Downloads/cardpricer
```

## Installation instructions (windows)
1. I have no fucking idea, go figure it out for yourself lol i don't use wendys. The conda folks have windows installation instructions so maybe you could do that? and then follow the same steps to make the conda environment? Let me know if you get it working and I'll add it to this readme.

## How to run the program to get prices

1. First, you need to have a csv file. Some requirements:
* the first column contains names of magic cards
* the csv file must have a header (column names)
* card names that include commas (i.e. "zada, hedron grinder") need to be wrapped in "", but your spreadsheet program should do this by default. LibreOffice Calc sure does. 
* card names need to be sort-of exact matches to scryfall card names, but are NOT case-sensitive and can be just the start of the name in the database. For example, "black lot" will match "Black Lotus", but "Avacyn's" will not match "Avacyn's Pilgrim" because there are multiple "Avacyn's" cards. 
* For split cards, use two slashes and spaces: "rise // fall". 
* For double-sided cards or cards with multiple names, you can just do one name. So "Dowsing Dagger" will find "Dowsing Dagger // Lost Vale". 
* No "1x naturalize" or any of that crap allowed. 
It's not the end of the world if you have some misspellings, because you'll just get a blank value for usd and an "error" set code + match name for those cards. See the included example file `neph_budget.csv` for reference. Remember, only the first column matters. The other columns will be carried through to your output, though.

2. activate your scrython conda environment with `conda activate scrython`

3. run the script. To run the example csv, you could do:
```
cd Downloads/cardpricer
python3 cardpricer.py -i neph_budget.csv -o test.csv
```
You could also run it on your own csv file using:
```
python3 ~/Downloads/cardpricer/cardpricer.py -i your_file.csv -o prices.csv
```

4. look at your output. You can check out the included example output `neph_budget_pricing.csv` to see what it will look like. 

5. deactivate conda environment when you're done with `conda deactivate`. Or just close the shell. Who cares?

## Planned features that will probably never materialize
* better error message handling when you mistype the input filepath. currently it's a typical python schmear of balogna that nobody wants to see.
* add some annoying ascii art that can't be disabled. shoot me some PRs with suggestions.
* ideally i'd like this thing to make you feel like you just downloaded a warez version of Quake 3 in 2001 and you're scared you'll break your dad's computer
* could return the max price and set if people wanted that (but why?)
* add a flag -j or --joke so that the program asks you "why did the phyrexian cross the road" and if you answer it wrong the program deletes itself
