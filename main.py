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
    await daily_w2g() # Call room generation function

@bot.command(name='watch',help="Play a video in the lastest watch2gether.")
async def watch(ctx, link):
    channel,msgs,last_scheduled,last_embed = await get_w2g_channel()
    # POST request  
    streamkey = os.environ['STREAMKEY']
    if streamkey == 'null':
      # Notify that there is no streamkey
      await channel.send("No streamkey found. Please create a new room.")
    url = f"https://w2g.tv/rooms/{streamkey}/sync_update"
    print(url)
    body = json.dumps({
      "w2g_api_key": f"{W2GAPI}",
      "item_url" : link
    }, separators=(',', ':'))
    data = requests.post(url,headers=headers,data=body)
    print(data)

@bot.command(name='queue',help="Add a video to the lastest watch2gether's playlist.")
async def queue(ctx, link):
    channel,msgs,last_scheduled,last_embed = await get_w2g_channel()
    # Currently the W2G API requires you to indivially name videos with the 'title' key.
    # So given a youtube URL I need to extract the videos title, so I can fill the 'title' key.
    # GET request
    if 'youtu' in link: # if youtube link grab title, since by default the link will be the title of the added queued video
      params = {"format": "json", "url": link}
      gurl = requests.Request("GET","https://www.youtube.com/oembed",params=params).prepare().url 
      data = requests.get(gurl).json()
      title = data['title']
    else: # tiktok, vimo, etc.
      title = link

    # POST request  
    # This is gonna need to be replaced so that it will grab the key from a previous message...
    streamkey = os.environ['STREAMKEY']
    if streamkey == 'null':
      # Notify that there is no streamkey
      await channel.send("No streamkey found. Please create a new room.")    
    purl = f"https://w2g.tv/rooms/{streamkey}/playlists/current/playlist_items/sync_update"
    print(purl)
    body = json.dumps({
      "w2g_api_key": f"{W2GAPI}",
      "add_items" : [{"url": link,"title": title}]
    }, separators=(',', ':'))
    print(body)
    data = requests.post(purl,headers=headers,data=body)
    print(data)

async def daily_w2g():
    channel,msgs,last_scheduled,last_embed = await get_w2g_channel()
    url = 'https://w2g.tv/rooms/create.json'
    body = json.dumps({
      "w2g_api_key": f"{W2GAPI}",
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
    await daily_w2g() # Call room generation function

async def get_w2g_channel():
    await bot.wait_until_ready() # Make sure your guild cache is ready so the channel can be found via get_channel
    channel = bot.get_guild(GUILD).get_channel(CHANNEL)
    bot_msgs = await channel.history(limit=50).filter(check_if_bot).flatten()
    # for loop to find last_scheduled embed
    bot_scheduled_msgs = [msg for msg in list(bot_msgs) if '17:00:0' in str(msg.created_at) or '05:00:0' in str(msg.created_at)]
    last_scheduled = bot_scheduled_msgs[0].created_at
    print("Last Scheduled Post:", last_scheduled)
    last_embed = bot_msgs[0].embeds # last !w2g command, may include user commands that won't have specific time...
    return channel, list(bot_msgs), last_scheduled, last_embed

def check_if_bot(msg):
    # Return True if the message is from this bot and if it is an embed link (i.e., embed strings have no characters)
    return bot.user.name in str(msg.author) and len(msg.content) == 0

async def set_WHEN():
    channel,msgs,last_scheduled,last_embed = await get_w2g_channel()
    # Case where the bot has no messages in channel
    if len(msgs) == 0:
        print("Creating first W2G link")
        await daily_w2g()
        channel,msgs,last_scheduled,last_embed = await get_w2g_channel() 
    
    # Re-define WHEN based on last scheduled post
    if '17:00:0' in str(last_scheduled):
        WHEN = time(5, 0, 0)
    elif '05:00:0' in str(last_scheduled):
        WHEN = time(17,0,0)
    else:
        print("Something has gone terribly wrong... Using default time...")  

    print('Scheduled Post Time:', datetime.combine(datetime.utcnow().date() + timedelta(days=1), WHEN))
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