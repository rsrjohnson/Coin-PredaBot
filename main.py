import discord
from discord.ext import commands
import os
from firebase_admin import credentials, initialize_app, storage
import pandas as pd
import datetime
import json
#import shutil
#import urllib.request
#import requests
#import re

from keep_alive import  keep_alive

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

#new_coins=False

#if new_coins:
  #update csvs

df_paprika=pd.read_csv('paprika_coin_data.csv')
df_gecko=pd.read_csv('gecko_coin_data.csv')

bot = commands.Bot(command_prefix='$')
    
@bot.event
async def on_ready():
  print('{0.user} is up and running'.format(bot))


@bot.command()
async def p(ctx,message,currency='usd'):

  coin_qry=message.lower()

  coin_id=df_gecko.loc[df_gecko['symbol']==coin_qry,'id'].iloc[0]
  #coin_id=re.findall(r'-+(.*)',coin_id)[0]

  #icon='https://raw.githubusercontent.com/TokenTax/cryptoicon-api/master/public/icons/128/color/'+coin_qry+'.png' 

  icon='https://raw.githubusercontent.com/rsrjohnson/Coin-PredaBot/main/icons/'+coin_qry+'.png'

  curr_price=cg.get_price(ids=coin_id, vs_currencies=currency.lower(),include_24hr_change=True)

  today=curr_price[coin_id][currency]
  change=round(curr_price[coin_id][currency+'_24h_change'],4)
  
  #yest=today-change
  #percent=round(change/yest*100,2)

  coloring=0xff0000
  

  if change > 0:  
    coloring=0x00ff00
    change='+'+str(change)
   

  #output='**price '+' '+ +'**\n' + '\n**24h change** '+' '+'**'+str(change)+'%**'
  
  embed = discord.Embed(title=coin_id,color=coloring)
  embed.add_field(name='price', value='**'+str(today) + ' '+ currency.upper()+'**', inline=False)
  embed.add_field(name='24h change', value='**'+str(change)+'%**', inline=False)

  embed.set_image(url=icon)
  await ctx.send(embed=embed)
 
  #discord.Embed(title="Hey", description="How are you?", color=colors[color_name])  
  


@bot.command()
async def candle(ctx,message,number_of_days=1):

    plt.clf()

    #time_frame=message.split()
    #number_of_days=int(time_frame[1])
    #coin=time_frame[0]


    #start_date = datetime.date(2019, 8 , 31) #yyyy-d-m
    #number_of_days = (datetime.date.today()-start_date).days
    
    number_of_days=int(number_of_days)
    
    coin_qry=message.upper()

    coin_id=df_paprika.loc[df_paprika['symbol']==coin_qry,'id'].iloc[0]
    #coin_id=re.findall(r'-+(.*)',coin_id)[0]
    

    start_date =datetime.date.today() - datetime.timedelta(days = number_of_days-1)

    candles_data={'data':[]}


    for i in range(number_of_days):
        date=(start_date + datetime.timedelta(days = i)).isoformat()
        candles_data['data'].append(cl.candles(coin_id, start=date)[0])

    df_candles = pd.json_normalize(candles_data['data'])

    fig = go.Figure(data=[go.Candlestick(x=df_candles['time_open'],
                open=df_candles['open'],
                high=df_candles['high'],
                low=df_candles['low'],
                close=df_candles['close'])])

    fig.update_layout(title=coin_id + ' last ' +str(number_of_days)+' days OHLC')
   
    #fig.show()
    filename = 'output.png'
    fig.write_image("output.png", engine="kaleido")

    fig.write_html("figure"+ coin_id +".html")
    file_html = "figure"+ coin_id +".html"
    bucket = storage.bucket()
    blob = bucket.blob(file_html)
    blob.upload_from_filename(file_html)

    blob.make_public()   

    #fig.savefig(filename)
    await ctx.send(file=discord.File(filename))
    await ctx.send(blob.public_url)

@bot.command()
async def gas(ctx,threshold):

  df_gas = pd.read_csv('gas_notes.csv',index_col=0)
  #n=df_gas.shape[0]  
  df_gas=df_gas.append({'threshold':[threshold],'user':[ctx.author.id]},ignore_index=True)

  df_gas.to_csv('gas_notes.csv')  

  await ctx.send('received')


@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)


token_auth = os.environ['TOKEN']

keep_alive()


bot.run(token_auth)