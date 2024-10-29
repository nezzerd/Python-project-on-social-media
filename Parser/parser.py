import json
import time
from abc import ABC, abstractmethod
from googleapiclient.discovery import build


class YouTubeAPI:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_video(self, video_id):
        return YouTubeVideo(self.youtube, video_id)

    def get_channel(self, channel_id):
        return YouTubeChannel(self.youtube, channel_id)


class YouTubeResource(ABC):
    def __init__(self, youtube, resource_id):
        self.youtube = youtube
        self.resource_id = resource_id
        self.metadata = self._fetch_metadata()

    @abstractmethod
    def _fetch_metadata(self):
        pass

    @abstractmethod
    def save_to_json(self, filename):
        pass


class YouTubeVideo(YouTubeResource):

    def _fetch_metadata(self):
        request = self.youtube.videos().list(
            part="snippet,statistics",
            id=self.resource_id
        )
        response = request.execute()
        video_info = response['items'][0]
        return {
            "title": video_info['snippet']['title'],
            "description": video_info['snippet']['description'],
            "tags": video_info['snippet'].get('tags', []),
            "published_at": video_info['snippet']['publishedAt'],
            "view_count": int(video_info['statistics'].get('viewCount', 0)),
            "like_count": int(video_info['statistics'].get('likeCount', 0)),
            "comment_count": int(video_info['statistics'].get('commentCount', 0))
        }

    def get_all_comments(self):
        comments = []
        request = self.youtube.commentThreads().list(
            part="snippet,replies",
            videoId=self.resource_id,
            maxResults=100
        )

        while request:
            response = request.execute()

            for item in response['items']:
                top_comment = item['snippet']['topLevelComment']['snippet']
                comment_data = {
                    "text": top_comment['textDisplay'],
                    "author": top_comment['authorDisplayName'],
                    "like_count": top_comment['likeCount'],
                    "published_at": top_comment['publishedAt'],
                    "replies": []
                }

                if "replies" in item:
                    for reply in item["replies"]["comments"]:
                        reply_data = {
                            "text": reply['snippet']['textDisplay'],
                            "author": reply['snippet']['authorDisplayName'],
                            "like_count": reply['snippet']['likeCount'],
                            "published_at": reply['snippet']['publishedAt']
                        }
                        comment_data["replies"].append(reply_data)

                comments.append(comment_data)

            if 'nextPageToken' in response:
                request = self.youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=self.resource_id,
                    maxResults=100,
                    pageToken=response['nextPageToken']
                )
                time.sleep(0.5)
            else:
                break
        print(f"Total top-level comments fetched: {len(comments)}")
        return comments

    def save_to_json(self, filename="video_data.json"):
        data = {
            "metadata": self.metadata,
            "comments": self.get_all_comments()
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


class YouTubeChannel(YouTubeResource):
    def _fetch_metadata(self):
        request = self.youtube.channels().list(
            part="snippet,statistics,contentDetails",
            id=self.resource_id
        )
        response = request.execute()
        channel_info = response['items'][0]
        return {
            "title": channel_info['snippet']['title'],
            "description": channel_info['snippet']['description'],
            "subscriber_count": int(channel_info['statistics'].get('subscriberCount', 0)),
            "view_count": int(channel_info['statistics'].get('viewCount', 0)),
        }

    def get_playlists(self):
        playlists = []
        request = self.youtube.playlists().list(
            part="snippet",
            channelId=self.resource_id,
            maxResults=50
        )

        while request:
            response = request.execute()
            for item in response['items']:
                playlists.append({
                    "playlist_id": item['id'],
                    "title": item['snippet']['title'],
                    "description": item['snippet'].get('description', '')
                })

            if 'nextPageToken' in response:
                request = self.youtube.playlists().list(
                    part="snippet",
                    channelId=self.resource_id,
                    maxResults=50,
                    pageToken=response['nextPageToken']
                )
            else:
                break

        return playlists

    def get_videos_in_playlist(self, playlist_id):
        videos = []
        request = self.youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50
        )

        while request:
            response = request.execute()
            for item in response['items']:
                videos.append({
                    "video_id": item['snippet']['resourceId']['videoId'],
                    "title": item['snippet']['title'],
                    "published_at": item['snippet']['publishedAt']
                })

            if 'nextPageToken' in response:
                request = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=response['nextPageToken']
                )
            else:
                break

        return videos

    def save_to_json(self, filename="channel_data.json"):
        data = {
            "title": self.metadata['title'],
            "description": self.metadata['description'],
            "subscriber_count": self.metadata['subscriber_count'],
            "view_count": self.metadata['view_count'],
            "playlists": []
        }

        playlists = self.get_playlists()
        for playlist in playlists:
            playlist_data = {
                "playlist_id": playlist["playlist_id"],
                "title": playlist["title"],
                "description": playlist["description"],
                "videos": self.get_videos_in_playlist(playlist["playlist_id"])
            }
            data["playlists"].append(playlist_data)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


api_key = 'api key here'
# 'AIzaSyCdetN9A5mano4odG01qjxzZ9XBKBw0wNk'
youtube_api = YouTubeAPI(api_key)

video_id = 'video id here'
# 'NAlVMKIJACg'
video = youtube_api.get_video(video_id)
video.save_to_json("video_data.json")

channel_id = 'channel id here'
# 'UCeKCxQDv6lWDSzuqUXGtMRA'
channel = youtube_api.get_channel(channel_id)
channel.save_to_json("channel_data.json")
