import json
import asyncio
import discord
from discord.ext import commands
import subprocess
from datetime import datetime, timedelta
from python_app.get_animes_and_mangas import all_embeds, load_all_embeds
from python_app.get_league_matches import get_future_league_games
from python_app.streamers_tracker import (
    get_top_stocks,
    get_specific_tickers,
    get_most_pumped,
)
from python_app.post_discord_webhook import (
    send_the_message,
)
from python_helpers import (
    create_webhook_url,
    create_stock_embed,
    get_ticker_embed,
    pumped_ticker_embed,
    get_all_live_embed,
)
from collections import OrderedDict
from operator import itemgetter

bot = commands.Bot(command_prefix="!")

with open("configuration.json") as json_file:
    config = json.load(json_file)


@bot.event
async def on_ready():

    TWITCH_CHANNEL_ID = 813935859002900500
    REFRESH_WHOS_LIVE_SECONDS = 300

    while True:
        embed = get_all_live_embed()
        channel = bot.get_channel(TWITCH_CHANNEL_ID)
        await channel.send(
            embed=embed, delete_after=float(REFRESH_WHOS_LIVE_SECONDS) + float(0.15)
        )
        await asyncio.sleep(REFRESH_WHOS_LIVE_SECONDS)


@bot.command(name="weeb")
async def weeb(ctx):
    print("started")
    dict_embeds = {}
    load_all_embeds()
    channels = await ctx.channel.webhooks()
    # print(all_embeds)
    # aa = sorted(all_embeds, key = lambda i: i['datetime'])
    for embed in all_embeds:
        embed_dict = embed.to_dict()
        dict_embeds[embed] = embed_dict.get("timestamp", "")
    dict_embeds = OrderedDict(
        sorted(dict_embeds.items(), key=itemgetter(1), reverse=True)
    )
    send_the_message(
        username="anime updates",
        webhook=create_webhook_url(channels[0].id, channels[0].token),
        avatar_url="https://media.discordapp.net/attachments/306941063497777152/792210065523998740/image.png",
        embeds=dict_embeds.keys(),
    )
    all_embeds.clear()


@bot.command(name="league")
async def league(ctx):
    future_games, future_embeds = get_future_league_games()
    for x in range(0, len(future_embeds)):
        if x < 7:
            # await ctx.send(future_games[x])
            await ctx.send(embed=future_embeds[x])


@bot.command(name="live")
async def live(ctx):
    embed = get_all_live_embed()
    await ctx.send(embed=embed)


@bot.command(name="stocks")
async def stocks(ctx):
    msg = message.content
    msg_array = msg.split(" ")
    from_date = None
    to_date = None
    if len(msg_array) == 2:
        from_date = msg_array[1]
    if len(msg_array) == 3:
        to_date = msg_array[2]

    # if no FROM DATE supplied, use 1 that is 2 days ago

    if not from_date:
        now = datetime.today() - timedelta(days=1)
        year = now.year
        month = now.month
        day = now.day
        from_date = str(year) + "-" + str(month) + "-" + str(day)

    top_stocks = get_top_stocks(from_date, to_date)
    await ctx.send(embed=create_stock_embed(top_stocks, from_date, to_date))
    # channels = await ctx.webhooks()
    # send_the_message(username="pop tickers", \
    #     webhook=create_webhook_url(channels[0].id, channels[0].token), \
    #     avatar_url=None, \
    #     content=top_stocks)
    # await ctx.send(top_stocks)


@bot.command(name="ticker")
async def ticker(ctx):
    msg = message.content
    msg_array = msg.split(" ")
    if len(msg_array) == 2:
        ticker = msg_array[1]
        print("!!! input ticker " + ticker)
        ticker_info = get_specific_tickers(ticker)
        if not ticker_info:
            await ctx.send("no tweets for this ticker found")
        ticker_embed = get_ticker_embed(ticker_info)
        if not ticker_embed:
            await ctx.send("no tweets for this ticker")
        await ctx.send(embed=ticker_embed)
    else:
        await ctx.send("enter a ticker")


@bot.command(name="pumped")
async def pumped(ctx):
    msg = message.content
    msg_array = msg.split(" ")
    from_date = None
    to_date = None

    if len(msg_array) == 2:
        from_date = msg_array[1]
        ticker = msg_array[0]

    else:
        from_date = None
        ticker = message.content

    if not from_date:
        now = datetime.today() - timedelta(days=3)
        year = now.year
        month = now.month
        day = now.day
        from_date = str(year) + "-" + str(month) + "-" + str(day)

    resp = get_most_pumped(from_date)
    embed = pumped_ticker_embed(resp, from_date)
    await ctx.send(embed=embed)


subprocess.Popen(["python3", "python_app/reset_twitter_script.py"])
bot.run(config.get("discordclientlogin"))


# @client.event
# async def on_message(message):
#     if message.content.startswith('!logstocks'):
#         for file_path in os.listdir("logs/"):
#             file = discord.File("logs/" + file_path)
#             await ctx.send(file=file)
