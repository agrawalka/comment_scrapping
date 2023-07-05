from flask import Flask, render_template, request
import os
import googleapiclient.discovery
import re
from nltk.sentiment import SentimentIntensityAnalyzer


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/scrapping", methods=["POST"])
def scrapping():
    url = request.form["urlInput"]

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    
    DEVELOPER_KEY = "API KEY"
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)
    # Function to extract video ID from the URL
    video_id = extract_video_id(url)
    # Function to fetch comments using the YouTube Data API
    comments,video_title = get_video_comments(youtube, video_id)

    pos_com = []
    net_com = []
    neg_com = []

    for comment,score in comments:
        if score >= 0.3:
            pos_com.append(comment)
        elif score == 0.0:
            net_com.append(comment)
        else:
            neg_com.append(comment)


    print(comments)

    return render_template("result.html",title=video_title,positive = pos_com,neutral=net_com, negative = neg_com)


def extract_video_id(url):

    split_url = url.split("v=") #every url has a "v="" part after which is mentioned the video id that we are looking for
    if len(split_url) > 1:  # this should be 2 in most cases
        video_id = split_url[1]
        return video_id
    else:
        return None


def get_video_comments(youtube, video_id):
    comments = []
    nextPageToken = None
    video_title = ""

    # Fetch video details
    video_response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()

    if video_response["items"]:
        video_title = video_response["items"][0]["snippet"]["title"]


    analyzer = SentimentIntensityAnalyzer()

    while True:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            pageToken=nextPageToken,
            maxResults=100
        ).execute()

        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            cleaned_comment = remove_emojis(comment)
            sentiment_score = get_sentiment_score(analyzer, cleaned_comment)
            comments.append((cleaned_comment, sentiment_score))

        nextPageToken = response.get("nextPageToken")

        if not nextPageToken:
            break

    return comments,video_title


def get_sentiment_score(analyzer, text):
    # Calculate sentiment score using the SentimentIntensityAnalyzer
    sentiment = analyzer.polarity_scores(text)
    return sentiment["compound"]


def remove_emojis(text):
    emoji_pattern = re.compile(
        pattern="["
                "\U0001F600-\U0001F64F"  # Emoticons
                "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
                "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
                "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
                "\U00002702-\U000027B0"  # Dingbats
                "\U000024C2-\U0001F251"  # Enclosed characters
                "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r"", text)



if __name__ == "__main__":
    app.run(debug=True)
