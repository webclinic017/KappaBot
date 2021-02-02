import discord, json
import subprocess
import requests
import importlib
from bs4 import BeautifulSoup, SoupStrainer
from python_app.get_animes_and_mangas import all_embeds, load_all_embeds
from python_app.get_league_matches import get_future_league_games
from python_app.streamers_tracker import get_platform_streamers, get_everyone_online, update_viewer_count
from python_app.post_discord_webhook import sendWebhookMessage, sendWebhookListEmbeds, send_the_message

client = discord.Client()

with open('configuration.json') as json_file :
    config = json.load(json_file)

def create_webhook_url(id, token):
    return "https://discordapp.com/api/webhooks/" + str(id) + "/" + str(token)

def update_youtube_view_count():     
    """
    Used for the !live command, get and update the live youtubers!
    """

    def get_live_viewers(channel_id):
        url = "https://www.youtube.com/channel/" + channel_id
        content = requests.get(url).text
        soup = BeautifulSoup(content)
        raw = soup.findAll('script')

        if len(raw) <= 28:
            return 0
        main_json_str = str(raw[27])[59:-10]
        main_json = json.loads(main_json_str)

        if "channelFeaturedContentRenderer" not in main_json["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]:
            # if it gets to here, user is live, need to get their URL
            return 0
        
        viewer_count = main_json["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["channelFeaturedContentRenderer"]["items"][0]["videoRenderer"]["shortViewCountText"]["runs"][0]["text"]
            
        return viewer_count

    for streamer in get_platform_streamers("youtube"):
        name = streamer[0]
        channel_id = streamer[1]

        viewer_count = get_live_viewers(channel_id)
        update_viewer_count(name, str(viewer_count))


@client.event
async def on_message(message):
    if message.content.startswith('!weeb'):
        load_all_embeds()
        channels = await message.channel.webhooks()
        send_the_message(username="anime updates", \
            webhook=create_webhook_url(channels[0].id, channels[0].token), \
            avatar_url="https://media.discordapp.net/attachments/306941063497777152/792210065523998740/image.png", \
            embeds=all_embeds)

        all_embeds.clear()

    if message.content.startswith('!league'):
        future_games, future_embeds = get_future_league_games()
        for x in range(0, len(future_games)):
            if x < 5:
                await message.channel.send(future_games[x])
                await message.channel.send(embed=future_embeds[x])

    if message.content.startswith('!live'):

        embed = discord.Embed(colour=discord.Colour(12320855))
        is_anyone_online = False

        update_youtube_view_count()

        for streamer in get_everyone_online():
            is_anyone_online = True
            name = streamer[0]
            viewer_count = streamer[4]
            embed.add_field(name=name, value="[" + viewer_count + " viewers](https://twitch.tv/" + name + ")")

        if not is_anyone_online:
            embed = discord.Embed(tite="no ones online...")

        await message.channel.send(embed=embed)

    if message.content.startswith('!test'):
        await message.channel.send("hello")

subprocess.Popen(["python3","python_app/live_youtube_check.py"])
subprocess.Popen(["python3","python_app/get_twitch_live.py"])
subprocess.Popen(["python3","python_app/post_anime_episode_updates.py"])
subprocess.Popen(["python3","python_app/tweet_posts.py", ">>", "~/.forever/kappabot_tweets.log"])

client.run(config.get("discordclientlogin"))
