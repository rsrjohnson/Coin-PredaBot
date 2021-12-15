import discord
from discord.ext import commands, tasks
import os
from firebase_admin import credentials, initialize_app, storage
import pandas as pd

import json
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
#opts.add_argument('-headless')

import datetime
#from datetime import datetime
#import schedule
#import asyncio
import time
#import shutil
#import urllib.request
#import requests
#import re

from server_flask import keep_alive

F_CRED = os.environ['FIREBASE_CRED']
cred = credentials.Certificate(json.loads(F_CRED))
initialize_app(cred, {'storageBucket': 'quickhtmlhost.appspot.com'})

os.system('pip install kaleido')

os.environ['MPLCONFIGDIR'] = os.getcwd() + "/configs/"
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from coinpaprika import client as Coinpaprika
cl = Coinpaprika.Client()

from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

df_paprika = pd.read_csv('paprika_coin_data.csv')
df_gecko = pd.read_csv('gecko_coin_data.csv')

intents = discord.Intents.none()
intents.reactions = True
intents.members = True
intents.guilds = True

#new_coins=False

#if new_coins:
#update csvs
#discord_cl=discord.Client()
bot = commands.Bot(command_prefix='$')


from itertools import cycle

status = cycle(['with Python','with Watching the Markets'])

@bot.event
async def on_ready():  
  print('{0.user} is up and running'.format(bot))  
  track_job.start()
  change_status.start()
  #gas_job.start()



@tasks.loop(seconds=10)
async def change_status():
  await bot.change_presence(activity=discord.Game(next(status)))

@tasks.loop(seconds=20)
async def track_job():
          
    df_coins = pd.read_csv('coin_notes.csv', index_col=0)
    m=df_coins.shape[0]
    i=0
    dropped=[]
    erase=False

    coins=df_coins['coin'].unique()

    dict_prices={}
    for c_ in coins:
      dict_prices[c_]=cg.get_price(ids=c_,
                                vs_currencies='usd',
                                include_24hr_change=False)
    
    while i<m:
      row_index=df_coins.index[i]
      target=float(df_coins.loc[row_index,'threshold'])

      #qry=df_coins.loc[row_index,'coin']

      #coin_idg = df_gecko.loc[df_gecko['symbol'] == qry, 'id'].iloc[0]
      coin_idg=df_coins.loc[row_index,'coin']
      curr_price = dict_prices[coin_idg]

      #dserver=df_coins.loc[i,'server']
      dchannel=df_coins.loc[row_index,'channel']
      channel = bot.get_channel(dchannel)
      #channel=discord_cl.get_channel(dchannel)

      #bot.get_guild(df_coins.loc[i,'server']).get_channel(dchannel)

      #user_id="{:.17f}".format(df_coins.loc[row_index,'user']).rstrip('0').rstrip('.')
      #user= await bot.fetch_user(int(user_id)+1)
      #user+" "+

      if df_coins.loc[row_index,'below'] and curr_price[coin_idg]['usd']>=target:
        #server = bot.get_server(dserver)
        
        #user=
        await channel.send(coin_idg + " "+ " reached "+ str(target) + " USD")
        #bot.loop.create_task(channel.send(qry + " "+ " reached "+ str(target) + " USD"))
        erase=True
        dropped.append(row_index)

      elif not df_coins.loc[row_index,'below'] and curr_price[coin_idg]['usd']<=target:
        
        await channel.send(coin_idg + " "+ " reached "+ str(target) + " USD")
        #bot.loop.create_task(channel.send(qry + " "+ " reached "+ str(target) + " USD"))
        erase=True
        dropped.append(row_index)

      i+=1

    if erase:  
      df_coins=df_coins.drop(dropped)
      df_coins.to_csv('coin_notes.csv')


@tasks.loop(seconds=30)
async def gas_job():
        
    df_gas = pd.read_csv('gas_notes.csv', index_col=0)
    m=df_gas.shape[0]
    i=0
    dropped=[]
    erase=False
    url = "https://etherscan.io/gastracker"

    driver = webdriver.Chrome(options=opts)

    driver.get(url)
    # this is just to ensure that the page is loaded
    time.sleep(3)

    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")
    gas_low = soup.find('span', {'id': 'spanLowPrice'})
    gas_avg = soup.find('span', {'id': 'spanAvgPrice'})
    gas_high = soup.find('span', {'id': 'spanHighPrice'})

    driver.close()

    low = list(gas_low.children)[0].contents[0]
    avg = list(gas_avg.children)[0]
    high = list(gas_high.children)[0]

    curr_gas = float(avg)

    while i<m:
      row_index=df_gas.index[i]
      target=float(df_gas.loc[row_index,'threshold'])
      
      dchannel=df_gas.loc[row_index,'channel']
      channel = bot.get_channel(dchannel)
  

      if curr_gas<=target:        
        await channel.send("ETH Gas reached "+ str(target) + " gwei")       
        erase=True
        dropped.append(row_index)      

      i+=1

    if erase:  
      df_gas=df_gas.drop(dropped)
      df_gas.to_csv('gas_notes.csv')


# @bot.command()
# async def help(ctx):
#   ctx.send



#Current price command
@bot.command()
async def p(ctx, message, currency='usd'):

    qry = message.lower()

    coin_idg = df_gecko.loc[df_gecko['symbol'] == qry, 'id'].iloc[0]
    #coin_id=re.findall(r'-+(.*)',coin_id)[0]

    icon = 'https://raw.githubusercontent.com/rsrjohnson/Coin-PredaBot/main/icons/' + qry + '.png'

    curr_price = cg.get_price(ids=coin_idg,
                              vs_currencies=currency.lower(),
                              include_24hr_change=True)

    today = curr_price[coin_idg][currency]
    change = round(curr_price[coin_idg][currency + '_24h_change'], 6)

    #yest=today-change
    #percent=round(change/yest*100,6)

    coloring = 0xff0000

    if change > 0:
        coloring = 0x00ff00
        change = '+' + str(change)

    embed = discord.Embed(title=coin_idg, color=coloring)
    embed.add_field(name='price',
                    value='**' + str(today) + ' ' + currency.upper() + '**',
                    inline=False)
    embed.add_field(name='24h change',
                    value='**' + str(change) + '%**',
                    inline=False)

    embed.set_image(url=icon)
    await ctx.send(embed=embed)

#Daily candles
@bot.command()
async def candle(ctx, message, number_of_days=1):

    plt.clf()

    #time_frame=message.split()
    #number_of_days=int(time_frame[1])
    #coin=time_frame[0]

    #start_date = datetime.date(2019, 8 , 31) #yyyy-d-m
    #number_of_days = (datetime.date.today()-start_date).days

    number_of_days = int(number_of_days)

    coin_qry = message.upper()
    coin_id = df_paprika.loc[df_paprika['symbol'] == coin_qry, 'id'].iloc[0]
    #coin_id=re.findall(r'-+(.*)',coin_id)[0]

    start_date = datetime.date.today() - datetime.timedelta(
        days=number_of_days - 1)

    candles_data = {'data': []}

    for i in range(number_of_days):
        date_ = (start_date + datetime.timedelta(days=i)).isoformat()
        candles_data['data'].append(cl.candles(coin_id, start=date_)[0])

    df_candles = pd.DataFrame(candles_data['data'])
    df_candles.columns = [
        'time_open', 'time_close', 'open', 'high', 'low', 'close', 'volume',
        'market_cap'
    ]

    fig = go.Figure(data=[
        go.Candlestick(x=df_candles['time_open'],
                       open=df_candles['open'],
                       high=df_candles['high'],
                       low=df_candles['low'],
                       close=df_candles['close'])
    ])

    fig.update_layout(title=coin_id + ' last ' + str(number_of_days) +
                      ' days OHLC')

    #fig.show()
    filename = 'output.png'
    fig.write_image("output.png", engine="kaleido")

    fig.write_html("figure" + coin_id + ".html")
    file_html = "figure" + coin_id + ".html"
    bucket = storage.bucket()
    blob = bucket.blob(file_html)
    blob.upload_from_filename(file_html)

    blob.make_public()   

    
    await ctx.send(file=discord.File(filename))
    await ctx.send(blob.public_url)

    os.remove("figure" + coin_id + ".html")
    os.remove('output.png')



@bot.command()
async def track(ctx,coin,threshold):

    qry = coin.lower()

    coin_idg = df_gecko.loc[df_gecko['symbol'] == qry, 'id'].iloc[0]
    #coin_id=re.findall(r'-+(.*)',coin_id)[0]

    

    curr_price = cg.get_price(ids=coin_idg,
                              vs_currencies='usd',
                              include_24hr_change=False)
    
    below=False

    if curr_price[coin_idg]['usd']<float(threshold):
      below=True

    df_coins = pd.read_csv('coin_notes.csv', index_col=0)
    #ld=[coin,threshold,below,ctx.message.guild.id,ctx.channel.id,ctx.author.id]

    #df_coins.loc[len(df_coins.index)] = ld

    #"{:.17f}".format(ctx.author.id).rstrip('0')    

    df_coins = df_coins.append(
        {   
            'coin':coin_idg,
            'threshold': threshold,
            'below':below,
            'server': ctx.message.guild.id,
            'channel':ctx.channel.id,
            'user': ctx.author.id
        },
        ignore_index=True)

    df_coins.to_csv('coin_notes.csv')

    await ctx.send('Alert activated, you will be notified when '+ coin + ' reaches '+ threshold+ ' USD\n'+ 'Current price is at '+ str(curr_price[coin_idg]['usd'])+ ' USD')

        
#Get current eth gas
@bot.command()
async def gas(ctx):

    url = "https://etherscan.io/gastracker"

    driver = webdriver.Chrome(options=opts)

    driver.get(url)
    # this is just to ensure that the page is loaded
    time.sleep(3)

    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")
    gas_low = soup.find('span', {'id': 'spanLowPrice'})
    gas_avg = soup.find('span', {'id': 'spanAvgPrice'})
    gas_high = soup.find('span', {'id': 'spanHighPrice'})

    driver.close()

    low = list(gas_low.children)[0].contents[0]
    avg = list(gas_avg.children)[0]
    high = list(gas_high.children)[0]

    await ctx.send('low: ' + low + ', avg: ' + avg + ', high: ' + high)

#Submit a gas threshold
@bot.command()
async def trackgas(ctx, threshold):

    df_gas = pd.read_csv('gas_notes.csv', index_col=0)
    #'server': [ctx.message.guild.id],
    #df_gas.loc[len(df_gas.index)] = ld
    df_gas = df_gas.append(
        {
            'threshold':threshold,            
            'channel':ctx.channel.id,
            'user': ctx.author.id
        },
        ignore_index=True)

    df_gas.to_csv('gas_notes.csv')

    await ctx.send('Alert activated, you will be notified when the gas price reaches ' + threshold + ' gwei.')


@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)




keep_alive()

token_auth = os.environ['TOKEN']


#bot.loop.create_task(track_job())
bot.run(token_auth)