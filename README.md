# Watch2GetherBot

## Author
Mathew Potts aka SirPottsalot

## Description
Discord Bot that posts a new Watch2Gether Link every 36 hours (lifetime of a temp Watch2Gether room). Uses a Replit web server in combination with UptimeRobot to keep the web server online indefinately. This isn't entirely true since there is a few minutes every day when Replit restarts the bot. To compensation for this when the bot starts it checks the last time it posted the Watch2Gether link was posted and posts it 36 hours after the last one.

## Commands
- !w2g
- !queue
- !add

## Troubleshooting

### Solved by '''kill 1''' in the replit’s shell tab to destroy the current container and switch to a new one. This will re-install discord.
  File "main.py", line 181, in <module>
    bot.run(TOKEN)
  File "/opt/virtualenvs/python3/lib/python3.8/site-packages/discord/client.py", line 723, in run
    return future.result()
  File "/opt/virtualenvs/python3/lib/python3.8/site-packages/discord/client.py", line 702, in runner
    await self.start(*args, **kwargs)
  File "/opt/virtualenvs/python3/lib/python3.8/site-packages/discord/client.py", line 665, in start
    await self.login(*args, bot=bot)
  File "/opt/virtualenvs/python3/lib/python3.8/site-packages/discord/client.py", line 511, in login
    await self.http.static_login(token.strip(), bot=bot)
  File "/opt/virtualenvs/python3/lib/python3.8/site-packages/discord/http.py", line 300, in static_login
    data = await self.request(Route('GET', '/users/@me'))
  File "/opt/virtualenvs/python3/lib/python3.8/site-packages/discord/http.py", line 216, in request
    raise HTTPException(r, data)
discord.errors.HTTPException: 429 Too Many Requests (error code: 0)

## Credits
- [Watch2Gether's Team](https://community.w2g.tv/t/watch2gether-api-documentation/133767)
- [freeCodeCamp.org](https://www.youtube.com/watch?v=SPTfmiYiuok)
- [Distorted Pumpkin](https://stackoverflow.com/questions/63769685/discord-py-how-to-send-a-message-everyday-at-a-specific-time)
- [Cynical-Badger](https://github.com/Cynical-Badger)