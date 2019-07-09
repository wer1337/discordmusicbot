# Discord Music Bot
This bot plays music through the use of youtube links.

To get this bot on your discord, Create a new discord app and find the Client ID.
Once you have the client ID, navigate to the link below using your own client ID.

`https://discordapp.com/oauth2/authorize?client_id=<CLIENTID>&scope=bot`

## Configuration
Before starting the bot, make sure you rename `app_config.yml.example` to `app_config.yml`.
Also be sure to use your own bot token that can be found on the discord developer console on your app.

## Requirements
Python 3.6+

```
aiohttp==3.3.2
async-timeout==3.0.0
attrs==18.1.0
cffi==1.11.5
chardet==3.0.4
discord.py==0.16.12
idna==2.7
idna-ssl==1.1.0
multidict==4.3.1
pycparser==2.18
PyNaCl==1.2.1
PyYAML==3.13
six==1.11.0
websockets==3.4
yarl==1.2.6
youtube-dl==2018.7.21
```