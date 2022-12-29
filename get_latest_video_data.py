# Reference : https://techtfq.com/video/python-project-to-scrape-youtube-using-youtube-data-api
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
# import datetime
import time # to check the efficiency of requests when #vids differ
import json #To save channel information
import re
# from config_dream import api_key,channel_id 
import os

api_key = os.environ['API_KEY']
channel_id = os.environ['CHANNEL_ID']

youtube = googleapiclient.discovery.build('youtube','v3',developerKey = api_key)

#Get channel information and return each values
def get_channel_info(youtube,channel_id) :
    request = youtube.channels().list(
        part = 'snippet,contentDetails,statistics',
        id = channel_id)
    response = request.execute()
    res_items = response['items'][0] #for convenience 
    channel_name = res_items['snippet']['title']
    num_subscribers = res_items['statistics']['subscriberCount']
    num_vid = res_items['statistics']['videoCount']
    total_views = res_items['statistics']['viewCount']
    playlist_id = res_items['contentDetails']['relatedPlaylists']['uploads']

    with open('latest_nct_dream_channel.json','w',encoding='utf-8') as f:
        json.dump(response,f,ensure_ascii=False,indent=4)
    return channel_name,num_subscribers,num_vid,total_views,playlist_id

# Retrieve a list of video id's of the channel - all vids
def get_video_id_list(youtube,playlist_id):
    request = youtube.playlistItems().list(
        part = 'contentDetails',
        playlistId = playlist_id,
        maxResults = 50)
        # publishedAfter ="2022-07-25T00:00:00Z") ->NEED TO FIGURE FORMAT
    response = request.execute()

    vid_id_list = []
    for i in range(len(response['items'])):
        vid_id_list.append(response['items'][i]['contentDetails']['videoId'])

    while (response.get('nextPageToken')):
        next_page_token = response.get('nextPageToken')
        request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId = playlist_id,
                maxResults = 50,
                pageToken = next_page_token)
        response = request.execute()
        for i in range(len(response['items'])):
            vid_id_list.append(response['items'][i]['contentDetails']['videoId'])

    return vid_id_list
    
# Retrieve the needed statistics of each video
def get_vid_stats(youtube, vid_id_list):
    vid_stats = []

    for i in range(0, len(vid_id_list),50):
        request = youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(vid_id_list[i:i+50])) #requestiong 50 at once is efficient
        response = request.execute()

        for video in response['items']:
            video_stats = [video['snippet']['title'],
                            video['snippet']['publishedAt'],
                            video['statistics']['viewCount'],
                            video['statistics']['likeCount'],
                            video['statistics']['commentCount'],
                            video['contentDetails']['duration']]
            vid_stats.append(video_stats)

    return vid_stats
# Request 50 videos at once for efficiency proven through test
# Requesting 50 at once - 0.38 seconds
# Requesting data individually - 8.88 seconds
# The cost of requesting is long, so less requests the better


# Rerefence : https://www.geeksforgeeks.org/find-all-the-numbers-in-a-string-using-regular-expression-in-python/
# Function to change duration of video from iso8601 to seconds
def convert_to_seconds(dur):
    arr = re.findall(r'[0-9]+', dur)
    if len(arr)==2 :
        return int(arr[0])*60+int(arr[1])
    elif len(arr)==3 :
        return int(arr[0])*3600+int(arr[1])*60 + int(arr[2])
    elif len(arr)==1 :
        return int(arr[0])

def isShorts(str):
    if "Shorts" in str:
        return True
    return False

def main():
    # Get statistics from channel
    playlist_id = get_channel_info(youtube, channel_id)[-1]
    #Get list of video id's
    vid_id_list = get_video_id_list(youtube, playlist_id)
    # Get a list of a list of stats of each video
    vid_stats = get_vid_stats(youtube, vid_id_list)
    
    # List of column names for dataframe
    cols = ['title','publishedAt','viewCount','likeCount','commentCount','duration']
    # Create dataframe
    df = pd.DataFrame(vid_stats,columns = cols)

    #Change duration data to seconds
    df['duration']=df['duration'].apply(convert_to_seconds)

    # Delete rows with "#Shorts" in title
    df = df.drop(df[df.title.apply(isShorts)==True].index)
    df.to_csv("latest_youtube_data.csv",index=False,encoding='utf-8-sig')
    
if __name__ == "__main__":
    main()