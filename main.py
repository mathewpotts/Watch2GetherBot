# Import Libs
import discord
import os
import requests
import json
from discord.ext import tasks, commands
from datetime import datetime, time, timezone
import asyncio
from keep_alive import keep_alive
import logger

# Setting the W2G room creation parameters
init_vid = "https://www.youtube.com/watch?v=lm6IU6V-dE8"  # Let's all go to the lobby
bg_color = "#000000"  # Black
bg_opacity = "50"

# Setting the default post time in UTC
POST_TIMES = [time(hour=17, tzinfo=timezone.utc)]

# Opening a log file
log = logger.Log('log.txt', max_lines=200)

# Setting command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Grabbing enviromental variables
TOKEN = os.environ['TOKEN']
W2GAPI = os.environ['W2G-API']
CHANNEL = int(os.environ['CHANNEL'])
GUILD = int(os.environ['GUILD'])

# Defining headers for W2G API
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}


@bot.event
async def on_ready():
  log.write(f'{bot.user.name} is connected to Discord.')
  daily_w2g.start()


@bot.command(name='w2g', help='Posts a new Watch2Gether Link.')
async def w2g(ctx):
  #log command
  log.write(f"{ctx.author.name} used !w2g command")
  await daily_w2g()  # Call room generation function
  
  


@bot.command(name='watch', help="Play a video in the lastest watch2gether.")
async def watch(ctx, link):
  channel = await get_w2g_channel()
  # POST request
  streamkey = os.environ['STREAMKEY']
  if streamkey == 'null':
    # Notify that there is no streamkey
    await channel.send("No streamkey found. Please create a new room.")
  url = f"https://api.w2g.tv/rooms/{streamkey}/sync_update"
  print(url)
  body = json.dumps({
      "w2g_api_key": f"{W2GAPI}",
      "item_url": link
  },
                    separators=(',', ':'))
  data = requests.post(url, headers=headers, data=body)
  print(data)
  #log command
  log.write(f"{ctx.author.name} used !watch {link}")


@bot.command(name='queue',
             help="Add a video to the lastest watch2gether's playlist.")
async def queue(ctx, link):
  channel = await get_w2g_channel()
  # Currently the W2G API requires you to indivially name videos with the 'title' key.
  # So given a youtube URL I need to extract the videos title, so I can fill the 'title' key.
  # GET request
  if 'youtu' in link:  # if youtube link grab title, since by default the link will be the title of the added queued video
    params = {"format": "json", "url": link}
    gurl = requests.Request("GET",
                            "https://www.youtube.com/oembed",
                            params=params).prepare().url
    data = requests.get(gurl).json()
    title = data['title']
  else:  # tiktok, vimo, etc.
    title = link

  # POST request
  # This is gonna need to be replaced so that it will grab the key from a previous message...
  streamkey = os.environ['STREAMKEY']
  if streamkey == 'null':
    # Notify that there is no streamkey
    await channel.send("No streamkey found. Please create a new room.")
  purl = f"https://api.w2g.tv/rooms/{streamkey}/playlists/current/playlist_items/sync_update"
  print(purl)
  body = json.dumps(
      {
          "w2g_api_key": f"{W2GAPI}",
          "add_items": [{
              "url": link,
              "title": title
          }]
      },
      separators=(',', ':'))
  print(body)
  data = requests.post(purl, headers=headers, data=body)
  print(data)
  #Log command
  log.write(f"{ctx.author.name} used !queue {link}")


@tasks.loop(time=POST_TIMES)
async def daily_w2g():
  channel = await get_w2g_channel()
  url = 'https://api.w2g.tv/rooms/create.json'
  body = json.dumps(
      {
          "w2g_api_key": f"{W2GAPI}",
          "share": init_vid,
          "bg_color": bg_color,
          "bg_opacity": bg_opacity
      },
      separators=(',', ':'))
  data = requests.post(url, headers=headers, data=body).json()
  print(data)
  os.environ['STREAMKEY'] = data['streamkey']
  streamkey = os.environ['STREAMKEY']
  keyem = discord.Embed(
      title=f'Here is the your Watch2Gether Link: \nhttps://w2g.tv/{streamkey}',
      description=
      'Watch2Gether lets you watch videos with your friends, synchronized at the same time.',
      color=16776960,
      url=f'https://w2g.tv/{streamkey}')
  keyem.set_thumbnail(url="https://w2g.tv/static/watch2gether-share.jpg")
  #Log info
  log.write(f"W2G Room created with key {streamkey}")
  await channel.send(embed=keyem)


async def get_w2g_channel():
  await bot.wait_until_ready(
  )  # Make sure your guild cache is ready so the channel can be found via get_channel
  channel = bot.get_guild(GUILD).get_channel(CHANNEL)

  log.write("Getting watch2gether channel.")

  return channel


def check_if_bot(msg):
  # Return True if the message is from this bot and if it is an embed link (i.e., embed strings have no characters)
  return bot.user.name in str(msg.author) and len(msg.content) == 0


if __name__ == "__main__":
  keep_alive()
  bot.run(TOKEN)
