import asyncio
import datetime
import discord
from discord.ext import commands
import yaml

from constants import CURRENT_VERSION as this_version

APP_CONFIG = None
bot = commands.Bot("~")
music_player_queue = []
currently_playing = None


# queue helper
def check_queue(ctx):
    global currently_playing
    currently_playing = None
    if music_player_queue:
        currently_playing = music_player_queue.pop(0)
        currently_playing.start()
        # Coroutines are not thread safe so you must call run threadsafe coroutine and call the future result
        coro = bot.send_message(ctx.message.channel, f"Now playing: {currently_playing.title}")
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        try:
            fut.result()
        except Exception as ex:
            print(f"Error: {repr(ex)}")
    else:
        coro = bot.send_message(ctx.message.channel, "There are no more songs to play!:scream: :scream:")
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        try:
            fut.result()
        except discord.DiscordException as ex:
            print(f"Exception occurred sending message: {repr(ex)}")


async def create_player(ctx, url):
    server = ctx.message.server
    voice_client = bot.voice_client_in(server)
    reconnect_options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 3"
    music_player = await voice_client.create_ytdl_player(url,
                                                         before_options=reconnect_options,
                                                         after=lambda: check_queue(ctx))
    return music_player


# starting up the bot
@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name=APP_CONFIG.get("bot_presence")))
    print(f"Welcome to MusicBot v{this_version}!")
    print("I am now ready and waiting!")


# first command
@bot.command()
async def hello():
    await bot.say("Yoyo! :wave:")


# joining the channel
@bot.command(pass_context=True)
async def join(ctx):
    # Get channel of whoever summoned the bot
    channel = ctx.message.author.voice.voice_channel

    try:
        await bot.join_voice_channel(channel)
    except discord.InvalidArgument as invalid_argument:
        print(f"Error trying to join channel: {repr(invalid_argument)}")
        await bot.say("You must be in a voice channel before summoning me in!")
    except discord.ClientException as c_exc:
        print(f"Error trying to join channel: {repr(c_exc)}")
        await bot.say("I can only be in one voice channel at a time!")


# leaving channel
@bot.command(pass_context=True)
async def leave(ctx):
    # Get the current server that the bot is in
    server = ctx.message.server
    voice_client = bot.voice_client_in(server)
    try:
        await voice_client.disconnect()
    except:
        pass


# music bot command - Play <yt URL>
# I want to make this later work with querying yt and a yt URL
@bot.command(pass_context=True)
async def play(ctx, url=None):
    global currently_playing
    if not bot.is_voice_connected(ctx.message.server):
        await bot.say("I'm not even connected to a voice channel...\n"
                      "Summon me into a voice channel first.")
    elif not url:
        await bot.say("You must supply a youtube link!")
    else:
        try:
            player = await create_player(ctx, url)
            if currently_playing:
                music_player_queue.append(player)
                await bot.say(f"{player.title} added to queue :notes:\n"
                              f"There is/are {len(music_player_queue) - 1} song(s) ahead.\n"
                              f"Use list_queue command to see which songs are next")
            else:
                await bot.say(":headphones: Let's JAM :headphones:")
                currently_playing = player
                player.start()
        except discord.DiscordException as d_exc:
            print(f"Exception occurred trying to play song: {repr(d_exc)}")


@bot.command()
async def current():
    if not currently_playing:
        await bot.say("No song is currently playing")
    else:
        await bot.say(f":arrow_forward: : {currently_playing.title}")


# pauses the music
@bot.command(pass_context=True)
async def pause(ctx):
    if not bot.is_voice_connected(ctx.message.server):
        await bot.say("I'm not even connected to a voice channel...")
    elif not currently_playing:
        await bot.say("There is no song currently playing to pause!")
    else:
        currently_playing.pause()


# Clears the queue and stops all music
@bot.command()
async def stop():
    global currently_playing
    music_player_queue.clear()  # clears queue
    if currently_playing:
        currently_playing.stop()
    currently_playing = None


# Plays the next song
# Calling 'stop' on the current stream player will trigger
#   the 'after' callable that was specified when making the player
@bot.command()
async def play_next():
    if not currently_playing:
        await bot.say("There is no song currently playing!")
    else:
        currently_playing.stop()


# resumes the music
@bot.command()
async def resume():
    if not currently_playing:
        await bot.say("There is no song to resume playing...")
    else:
        currently_playing.resume()


@bot.command(pass_context=True)
async def list_queue(ctx):
    if len(music_player_queue) == 0:
        await bot.say("The music queue is empty! :cry:")
    else:
        # Create a nice embed for shits and giggles
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name="Song Queue")
        i = 1
        for player in music_player_queue:
            duration = datetime.timedelta(seconds=player.duration)
            embed.add_field(name=f"{i}. {player.title}", value=f"{duration}", inline=False)
            i += 1
        await bot.send_message(ctx.message.channel, embed=embed)


# command to add a song to the front of the queue
@bot.command(pass_context=True)
async def add_front(ctx, url=None):
    if url is None:
        await bot.say("You must supply a URL to play!")
    elif len(music_player_queue) == 0 or not currently_playing:
        await bot.say("Use the play command when there is no song playing or no songs lined up")
    else:
        player = await create_player(ctx, url)
        music_player_queue.insert(0, player)
        await bot.say(f"{player.title} added to front of queue.\n"
                      f"Use list_queue to see the updated queue.")


# Removes the specified song from the queue
@bot.command()
async def remove_song(index=None):
    if index is None:
        await bot.say("You must supply the index of the song you want to remove")
    else:
        index = int(index) - 1
        if len(music_player_queue) == 0:
            await bot.say("The queue is empty :face_palm:, nothing to remove...")
        elif index > len(music_player_queue) - 1:
            await bot.say("That index it out of the queue size!")
        else:
            player = music_player_queue.pop(index)
            await bot.say(f"{player.title} removed from the queue.\n"
                          f"Use list_queue to see the updated queue.")


@bot.command(pass_context=True)
async def replay(ctx, num_times=1):
    if num_times < 1:
        await bot.say("You can't replay a song 0 times...")
    else:
        current_url = currently_playing.url
        for _ in range(num_times):
            player = await create_player(ctx, current_url)
            music_player_queue.insert(0, player)
        await bot.say(f"Replaying {currently_playing.title} {num_times} time(s)")


@bot.command()
async def put_first(index=0):
    if len(music_player_queue) == 0:
        await bot.say("There are no songs in the queue.")
    elif index > len(music_player_queue) - 1:
        await bot.say(f"There is no {index} in the queue!")
    else:
        music_player_queue.insert(0, music_player_queue.pop(index - 1))
        await bot.say("The queue has updated!\n"
                      "Use list_queue to see the updated queue.")


# Command to display what each command does
@bot.command(pass_context=True)
async def commands(ctx):
    author = ctx.message.author

    embed = discord.Embed(
        colour=discord.Colour.red()
    )

    embed.set_author(name='Commands')
    embed.add_field(name='~hello', value='Says hello back', inline=False)
    embed.add_field(name='~join', value='Joins the channel the user is in', inline=False)
    embed.add_field(name='~disconnect', value='Leaves the channel', inline=False)
    embed.add_field(name='~play <youtube URL>', value='Plays the sound from the YT URL', inline=False)
    embed.add_field(name='~pause', value='Pause the music.', inline=False)
    embed.add_field(name='~resume', value='Resumes last played', inline=False)
    embed.add_field(name='~play_next', value='Plays the next song in the queue', inline=False)
    embed.add_field(name='~stop', value='Removes all the songs from the queue', inline=False)

    await bot.send_message(author, embed=embed)


if __name__ == "__main__":
    with open("app_config.yml", "r") as config_file:
        APP_CONFIG = yaml.safe_load(config_file)

    try:
        bot.run(APP_CONFIG.get("bot_token"))
    except Exception as ex:
        print(f"Exception occurred trying to run the bot: {repr(ex)}")
