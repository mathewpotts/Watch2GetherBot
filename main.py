#!/usr/bin/python3

# Import Libs
import discord
import os
import requests
import json
from discord.ext import tasks, commands
from datetime import time, timezone
import logging

# set up logging
logging.basicConfig(filename='/home/potts/w2g.log',
                    filemode='w',
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

# Setting the W2G room creation parameters
init_vid = "https://www.youtube.com/watch?v=lm6IU6V-dE8"  # Let's all go to the lobby
bg_color = "#000000"  # Black
bg_opacity = "50"

# Setting the default post time in UTC
POST_TIMES = [time(hour=19, tzinfo=timezone.utc)]

# Setting command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Grabbing enviromental variables
with open('/home/potts/git/Watch2GetherBot/keys.txt','r') as f:
    keys = f.read().split('\n')
W2GAPI = keys[0]
CHANNEL = int(keys[1])
GUILD = int(keys[2])
STREAMKEY = keys[3]
TOKEN = keys[4]

# Defining headers for W2G API
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

@bot.event
async def on_ready():
  logging.info(f'{bot.user.name} is connected to Discord.')
  try:
      await bot.tree.sync() # sync commands
      logging.info("Commands synced.")
  except:
      logging.debug("Commands not synced.")
  daily_w2g.start()


@bot.tree.command(name='w2g', description='Posts a new Watch2Gether Link.')
async def w2g(ctx: discord.Interaction):
  #log command
  logging.info(f"{ctx.user} used !w2g command")
  await daily_w2g()  # Call room generation function

@bot.tree.command(name='watch', description="Play a video in the lastest watch2gether.")
async def watch(ctx: discord.Interaction, link: str):
  channel = await get_w2g_channel()
  # POST request
  streamkey = os.environ['STREAMKEY']
  if streamkey == 'null':
    # Notify that there is no streamkey
    await channel.send("No streamkey found. Please create a new room.")
  url = f"https://api.w2g.tv/rooms/{streamkey}/sync_update"
  #print(url)
  body = json.dumps({
      "w2g_api_key": f"{W2GAPI}",
      "item_url": link
  },
                    separators=(',', ':'))
  data = requests.post(url, headers=headers, data=body)
  #print(data)
  #log command and data
  logging.debug(f"{data}")
  logging.info(f"{ctx.user} used !watch {link}")


@bot.tree.command(name='queue',
             description="Add a video to the lastest watch2gether's playlist.")
async def queue(ctx: discord.Interaction, link: str):
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
  #print(purl)
  body = json.dumps(
      {
          "w2g_api_key": f"{W2GAPI}",
          "add_items": [{
              "url": link,
              "title": title
          }]
      },
      separators=(',', ':'))
  #print(body)
  data = requests.post(purl, headers=headers, data=body)
  #print(data)
  #Log command
  logging.debug(f"{data}")
  logging.debug(f"{ctx.user} used !queue {link}")


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
  logging.debug(f"{data}")
  logging.debug(f"W2G Room created with key {streamkey}")
  await channel.send(embed=keyem)


async def get_w2g_channel():
  await bot.wait_until_ready(
  )  # Make sure your guild cache is ready so the channel can be found via get_channel
  channel = bot.get_guild(GUILD).get_channel(CHANNEL)

  logging.info("Getting watch2gether channel.")

  return channel


def check_if_bot(msg):
  # Return True if the message is from this bot and if it is an embed link (i.e., embed strings have no characters)
  return bot.user.name in str(msg.author) and len(msg.content) == 0


if __name__ == "__main__":
  bot.run(TOKEN, log_handler=None)
