# Import Libs
import discord
import os
import requests
import json
from discord.ext import commands
from datetime import datetime, time, timedelta
import asyncio
from keep_alive import keep_alive
import logger

# Setting the W2G room creation parameters
init_vid = "https://www.youtube.com/watch?v=lm6IU6V-dE8" # Let's all go to the lobby
bg_color = "#000000" # Black
bg_opacity = "50"

# Setting the time for Post time as a global variable
global WHEN 
WHEN = time(17,0,0) # Default post time

# Setting number of hours between scheduled posts
dt = 36  

# Opening a log file
log = logger.Log('log.txt',max_lines=200)

# Setting command prefix
bot = commands.Bot(command_prefix='!')

# Grabbing enviromental variables
TOKEN   = os.environ['TOKEN']
W2GAPI  = os.environ['W2G-API']
CHANNEL = int(os.environ['CHANNEL'])
GUILD   = int(os.environ['GUILD'])

# Defining headers for W2G API
headers =  {
  'Accept': 'application/json',
  'Content-Type': 'application/json'
}
      
@bot.event
async def on_ready():
    log.write(f'{bot.user.name} is connected to Discord.')

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
      "share" : init_vid,
      "bg_color" : bg_color,
      "bg_opacity" : bg_opacity
    }, separators=(',', ':'))
    data = requests.post(url,headers=headers,data=body).json()
    print(data)
    os.environ['STREAMKEY'] = data['streamkey']
    streamkey = os.environ['STREAMKEY']
    keyem = discord.Embed(
      title = f'Here is the your Watch2Gether Link: \nhttps://w2g.tv/rooms/{streamkey}', 
      description = 'Watch2Gether lets you watch videos with your friends, synchronized at the same time.',
      color = 16776960,
      url = f'https://w2g.tv/rooms/{streamkey}'
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
    last_scheduled = bot_scheduled_msgs[0].created_at.replace(second=0,microsecond=0)
    log.write(f'''Last Scheduled Post: {last_scheduled}''')
    last_embed = bot_msgs[0].embeds # last !w2g command, may include user commands that won't have specific time...
    return channel, list(bot_msgs), last_scheduled, last_embed

def check_if_bot(msg):
    # Return True if the message is from this bot and if it is an embed link (i.e., embed strings have no characters)
    return bot.user.name in str(msg.author) and len(msg.content) == 0

async def set_WHEN():
    channel,msgs,last_scheduled,last_embed = await get_w2g_channel()

    # Case where the bot has no messages in channel
    if len(msgs) == 0:
        log.write("No bot messages in this channel. Creating first W2G link",warn=True)
        await daily_w2g()
        channel,msgs,last_scheduled,last_embed = await get_w2g_channel() 
    
    # Post every 36 hours and write to log
    WHEN = last_scheduled + timedelta(hours=dt)
    log.write(f'Preliminary Scheduled Post Time: {WHEN}')
    return WHEN

async def background_task():
    while True:
        now = datetime.utcnow() # You can do now() or a specific timezone if that matters, but I'll leave it with utcnow
        target_time = await set_WHEN() # preliminary target time
        t_diff = target_time - now
        # Maybe change to a while loop that ends when t_diff is greater than 0. This would ensure that t_diff is positive no matter how many days it doesn't post 
        if t_diff.total_seconds() < 0: # if the time difference is less than 0, set target_time to one day from preliminary target_time.
            target_time = datetime.combine(target_time.date()+timedelta(days=1),target_time.time())
            log.write(f't_diff less than 0 ({t_diff.total_seconds()/3600} hours). Modifying target_time.',warn=True)
        log.write(f'Scheduled Post Time - {target_time}')
        seconds_until_target = (target_time - now).total_seconds()
        log.write(f'Sleeping for {seconds_until_target/3600} hours')
        await asyncio.sleep(seconds_until_target)  # Sleep until we hit the target time
        log.write(f'WHILE: Posting link in discord.')
        await called_once_a_day()  # Call the helper function that sends the message

if __name__ == "__main__":
  bot.loop.create_task(background_task())
  keep_alive()
  bot.run(TOKEN)