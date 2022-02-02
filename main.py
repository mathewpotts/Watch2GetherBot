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

# Setting the time for Post time as a global variable
global WHEN 
WHEN = time(17,0,0) 

# Setting command prefix
bot = commands.Bot(command_prefix='!')

# Defining headers for W2G API
headers =  {
  'Accept': 'application/json',
  'Content-Type': 'application/json'
}
      
@bot.event
async def on_ready():
    print(f'{bot.user.name} is connected to Discord.\n')

# Not needed at the moment maybe a future idea
#@bot.event
#async def on_message(msg):
#    if msg.author.bot and bot.user.name in str(msg.author):
#        print(os.environ['STREAMKEY'])
#    await bot.process_commands(msg)

@bot.command(name='w2g', help='Posts a new Watch2Gether Link.')
async def w2g(ctx):
    await daily_w2g()

@bot.command(name='watch',help="Play a video in the lastest watch2gether.")
async def watch(ctx, link):
    # Define Watch2gether channel object
    channel = bot.get_guild(GUILD).get_channel(CHANNEL)
    # POST request  
    streamkey = os.environ['STREAMKEY']
    if streamkey == 'null':
      # Notify that there is no streamkey
      await channel.send("No streamkey found. Please create a new room.")
    url = "https://w2g.tv/rooms/{0}/sync_update".format(streamkey)
    print(url)
    body = json.dumps({
      "w2g_api_key": "{0}".format(W2GAPI),
      "item_url" : link
    }, separators=(',', ':'))
    data = requests.post(url,headers=headers,data=body)
    print(data)

@bot.command(name='queue',help="Add a video to the lastest watch2gether's playlist.")
async def queue(ctx, link):
    # Define Watch2gether channel object
    channel = bot.get_guild(GUILD).get_channel(CHANNEL)
    # Currently the W2G API requires you to indivially name videos with the 'title' key.
    # So given a youtube URL I need to extract the videos title, so I can fill the 'title' key.
    # GET request
    if 'youtu' in link: # if youtube link grab title
      params = {"format": "json", "url": link}
      gurl = requests.Request("GET","https://www.youtube.com/oembed",params=params).prepare().url 
      data = requests.get(gurl).json()
      title = data['title']
    else: # tiktok, vimo, etc.
      title = link

    # POST request  
    streamkey = os.environ['STREAMKEY']
    if streamkey == 'null':
      # Notify that there is no streamkey
      await channel.send("No streamkey found. Please create a new room.")    
    purl = "https://w2g.tv/rooms/{0}/playlists/current/playlist_items/sync_update".format(streamkey)
    print(purl)
    body = json.dumps({
      "w2g_api_key": "{0}".format(W2GAPI),
      "add_items" : [{"url": link,"title": title}]
    }, separators=(',', ':'))
    print(body)
    data = requests.post(purl,headers=headers,data=body)
    print(data)

async def daily_w2g():
    # Define Watch2gether channel object
    channel = bot.get_guild(GUILD).get_channel(CHANNEL)
    url = 'https://w2g.tv/rooms/create.json'
    body = json.dumps({
      "w2g_api_key": "{0}".format(W2GAPI),
      "share" : "https://www.youtube.com/watch?v=lm6IU6V-dE8", # Let's all go to the lobby
      "bg_color" : "#000000", # Black
      "bg_opacity" : "50"
    }, separators=(',', ':'))
    data = requests.post(url,headers=headers,data=body).json()
    print(data)
    os.environ['STREAMKEY'] = data['streamkey']
    streamkey = os.environ['STREAMKEY']
    keyem = discord.Embed(
      title = 'Here is the your Watch2Gether Link: \nhttps://w2g.tv/rooms/'+ streamkey, 
      description = 'Watch2Gether lets you watch videos with your friends, synchronized at the same time.',
      color = 16776960,
      url = 'https://w2g.tv/rooms/' + streamkey
    )
    keyem.set_thumbnail(url="https://w2g.tv/static/watch2gether-share.jpg") 
    await channel.send(embed = keyem)

async def called_once_a_day():  # Fired every day
    await bot.wait_until_ready()  # Make sure your guild cache is ready so the channel can be found via get_channel
    await daily_w2g() 

def check_if_bot(msg):
    # Return True if the message is from this bot and if it is an embed link (i.e., embed strings have no characters)
    return bot.user.name in str(msg.author) and len(msg.content) == 0

async def set_WHEN():
    await bot.wait_until_ready()
    channel = bot.get_guild(GUILD).get_channel(CHANNEL)
    msgs = await channel.history(limit=50).filter(check_if_bot).flatten()
    
    # Case where the bot has no messages in channel
    if len(msgs) == 0:
        print("Creating first W2G link")
        await daily_w2g()
        msgs = list(await channel.history().filter(check_if_bot)) #last message
    
    # Re-define WHEN based on last link post time
    if '17:00' in str(msgs[0].created_at):
        WHEN = time(5, 0, 0)
    elif '5:00' in str(msgs[0].created_at):
        WHEN = time(17,0,0)
    else:
        print("Something has gone terribly wrong...")

    print(f'Setting post time to {WHEN}')
    return WHEN

async def background_task():
    now = datetime.utcnow()
    WHEN = await set_WHEN()
    #print(now,WHEN)
    if now.time() > WHEN:  # Make sure loop doesn't start after {WHEN} as then it will send immediately the first time as negative seconds will make the sleep yield instantly
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
        await asyncio.sleep(seconds)   # Sleep until tomorrow and then the loop will start 
    while True:
        now = datetime.utcnow() # You can do now() or a specific timezone if that matters, but I'll leave it with utcnow
        target_time = datetime.combine(now.date(), WHEN)  # 17:00 pm today (In UTC)
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