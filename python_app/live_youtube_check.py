import json, requests, sched, time, logging
# from bs4 import BeautifulSoup
from discord import RequestsWebhookAdapter, Webhook
from bs4 import BeautifulSoup
from WEBHOOKS import webhooks
from streamers_tracker import add_utube_link, does_utube_link_exist, get_platform_streamers, get_video_id, update_video_id, get_who_to_at
from logging.handlers import RotatingFileHandler

with open('./configuration.json') as json_file :
    config = json.load(json_file)

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

    
logger = logging.getLogger("Rotating Log")
handler = RotatingFileHandler('logs/live-youtube-check.log', maxBytes=7000000, backupCount=5)
handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%dT%H:%M:%S%z"))
logger.addHandler(handler)


def get_latest_video_in_channel(channel_id):
    api_key = config.get("gKey")

    base_video_url = 'https://www.youtube.com/watch?v='
    base_search_url = 'https://www.googleapis.com/youtube/v3/search?'

    first_url = base_search_url+'key={}&channelId={}&part=snippet,id&order=date&maxResults=1&broadcastStatus=active'.format(api_key, channel_id)

    logger.info(first_url)

    video_links = []
    url = first_url

    resp = requests.get(url)

    if resp.status_code == 200:
        
        resp = json.dumps(resp.json())
        resp = json.loads(resp)
        logger.info(resp)

        first_url = resp["items"][0]["id"]["videoId"]
        title = resp["items"][0]["snippet"]["title"]

    else:
        return None, None

    logger.info('got title, first_url' )
    logger.info(title)
    logger.info(first_url)
    return (title, first_url)


def get_filtered_video(channel_name, channel_id, filter_str):
    
    [name, url] = get_latest_video_in_channel(channel_id)
    
    if not name:
        return None

    if filter_str:
        filters = filter_str.split(",")
    else:
        filters = None

    if not filters:
        url = "https://www.youtube.com/watch?v=" + url
        return url

    
    if name[0] == "E":
        url = "https://www.youtube.com/watch?v=" + url
        return url

    for filter in filters:
        if filter.lower() in name.lower():
            url = "https://www.youtube.com/watch?v=" + url
            return url

    return None


def check_if_url_in_db(channel_name, last_video_id):
    saved_video_id = get_video_id(channel_name)

    if saved_video_id != last_video_id:
        return False

    return True


def get_last_youtube_video_id(channel_id):
    url = "https://www.youtube.com/channel/" + channel_id
    content = requests.get(url).text
    soup = BeautifulSoup(content)
    raw = soup.findAll('script')

    if len(raw) < 29:
        return None

    main_json_str = str(raw[27])[59:-10]
    main_json = json.loads(main_json_str)
    url = None

    try:
        video_id =(main_json["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["itemSectionRenderer"]["contents"][0]["shelfRenderer"]["content"]["horizontalListRenderer"]["items"][0]["gridVideoRenderer"]["videoId"])
        url = "https://www.youtube.com/watch?v=" + video_id
    except:
        return None

    return url


def check_youtube_live(channel_id):
    api_key = config.get("gKey")

    base_video_url = 'https://www.youtube.com/watch?v='
    base_search_url = 'https://www.googleapis.com/youtube/v3/search?'

    first_url = base_search_url+'key={}&channelId={}&part=snippet,id&order=date&maxResults=1&type=video&eventType=live'.format(api_key, channel_id)

    logger.info(first_url)

    video_links = []
    url = first_url

    resp = requests.get(url)

    if resp.status_code == 200:
        
        resp = json.dumps(resp.json())
        resp = json.loads(resp)

        first_url = resp["items"][0]["id"]["videoId"]
        title = resp["items"][0]["snippet"]["title"]

    else:

        logger.info('!!!!')
        logger.info(resp.status_code)
        logger.info(resp.text)
        return None, None

    logger.info('got title, first_url' )
    logger.info(title)
    logger.info(first_url)
    return (title, first_url)


def start_youtube_checks(scheduler):

    for streamer in get_platform_streamers("youtube"):
        time.sleep(.5)
        logger.info("  Streamer info loaded: " + str(streamer))
        name = streamer[0]
        channel_id = streamer[1]
        last_video_id = streamer[2]
        is_online = streamer[3]
        viewer_count = streamer[4]
        filter_str = streamer[6]
        who_to_at_str = streamer[7]

        if channel_id:
            # # IF ITS ICE, we take BETTER PRECAUTIONS!!!!!!!!!!!!!!! or dip
            # if channel_id == "UCv9Edl_WbtbPeURPtFDo-uA" or channel_id == "UCakgsb0w7QB0VHdnCc-OVEA":
            # #  or channel_id == "UC3Nlcpu-kbLmdhph_BN7OwQ":
            #     logger.info("BEGINNING ICE CHECKS")
            #     logger.info("BEGINNING ICE CHECKS")
            #     logger.info("BEGINNING ICE CHECKS")
            #     live_url = check_youtube_live(channel_id)
                
            #     if live_url:
            #         logger.info("ICE is online! with URL : " + live_url)
            #         update_video_id(name, live_url)
            #         if not is_online:
            #             sendWebhookMessage(w, "<@173610714433454084> <@173611085671170048> " + name + " IS LIVE " + "https://www.youtube.com/watch?v=" + live_url)
            #         update_streamer_online_status(name, "TRUE")
            #     if not live_url:
            #         logger.info("ICE is offline!!!")
            #         update_streamer_online_status(name, "FALSE")
            #         update_video_id(name, "NULL")

            last_youtube_video = get_filtered_video(name, channel_id, filter_str)
            if last_youtube_video and last_youtube_video != last_video_id and not does_utube_link_exist(last_youtube_video):
                who_to_at_discord_ats = get_who_to_at(who_to_at_str)
                # print("output")
                # print(does_utube_link_exist(last_youtube_video))
                # if not does_utube_link_exist(last_youtube_video):
                sendWebhookMessage(webhooks.YOUTUBE_VIDS.value, name, last_youtube_video + " " + who_to_at_discord_ats)

                add_utube_link(last_youtube_video)
                update_video_id(name, last_youtube_video)

    scheduler.enter(900, 1, start_youtube_checks, (scheduler,))


def sendWebhookMessage(webhook, name, body_to_post):

    webhook = Webhook.from_url(url = webhook, adapter = RequestsWebhookAdapter())

    webhook.send(body_to_post, avatar_url="https://upload.wikimedia.org/wikipedia/commons/9/99/Paul_denino_13-01-19.jpg")


def start_live_checks():
    s = sched.scheduler(time.time, time.sleep)
    s.enter(1, 1, start_youtube_checks, (s,))
    s.run()


start_live_checks()


def update_youtube_view_count():
    for streamer in get_platform_streamers("youtube"):
        name = streamer[0]
        channel_id = streamer[1]

        viewer_count = get_live_viewers(channel_id)
        update_viewer_counts(name, viewer_count)


# if __name__ == "__main__":
#     logger.info(check_youtube_live("UCESLZhusAkFfsNsApnjF_Cg"))

