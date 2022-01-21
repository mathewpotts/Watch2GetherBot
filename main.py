# Import Libs
import discord
import os
import requests
import json
from discord.ext import commands
from datetime import datetime, time, timedelta
import asyncio
from keep_alive import keep_alive

# Grabbing enviromental variables
TOKEN   = os.environ['TOKEN']
W2GAPI  = os.environ['W2G-API']
CHANNEL = int(os.environ['CHANNEL'])
GUILD   = int(os.environ['GUILD'])

# Setting the time for Post time
WHEN = time(10, 0, 0)  # 10:00 am (3 am MT) 

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user.name} is connected to Discord.\n')

@bot.command(name='w2g', help='Posts a new Watch2Gether Link.')
async def w2g(ctx):
    await daily_w2g()

async def daily_w2g():
    url = 'https://w2g.tv/rooms/create.json'
    headers =  {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
    body = json.dumps({
      "w2g_api_key": "{0}".format(W2GAPI),
      "share" : "https://www.youtube.com/watch?v=lm6IU6V-dE8", # Let's all go to the lobby
      "bg_color" : "#000000",
      "bg_opacity" : "50"
    }, separators=(',', ':'))
    data = requests.post(url,headers=headers,data=body).json()
    print(data)
    streamkey = data['streamkey']
    keyem = discord.Embed(
      title = 'Here is the your Watch2Gether Link: \nhttps://w2g.tv/rooms/'+ streamkey, 
      description = 'Watch2Gether lets you watch videos with your friends, synchronized at the same time.',
      color = 16776960,
      url = 'https://w2g.tv/rooms/' + streamkey
    )
    keyem.set_thumbnail(url="https://w2g.tv/static/watch2gether-share.jpg")
    channel = bot.get_guild(GUILD).get_channel(CHANNEL) 
    await channel.send(embed = keyem)
    
async def called_once_a_day():  # Fired every day
    await bot.wait_until_ready()  # Make sure your guild cache is ready so the channel can be found via get_channel
    await daily_w2g() 

async def background_task():
    now = datetime.utcnow()
    if now.time() > WHEN:  # Make sure loop doesn't start after {WHEN} as then it will send immediately the first time as negative seconds will make the sleep yield instantly
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
        await asyncio.sleep(seconds)   # Sleep until tomorrow and then the loop will start 
    while True:
        now = datetime.utcnow() # You can do now() or a specific timezone if that matters, but I'll leave it with utcnow
        target_time = datetime.combine(now.date(), WHEN)  # 6:00 PM today (In UTC)
        seconds_until_target = (target_time - now).total_seconds()
        await asyncio.sleep(seconds_until_target)  # Sleep until we hit the target time
        await called_once_a_day()  # Call the helper function that sends the message
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
        await asyncio.sleep(seconds)   # Sleep until tomorrow and then the loop will start a new iteration


if __name__ == "__main__":
  bot.loop.create_task(background_task())
  keep_alive()
  bot.run(TOKEN)