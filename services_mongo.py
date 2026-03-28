from typing import List, Dict, Any, Optional
from mongo_client import MongoDBClient

class MongoService:
    def __init__(self):
        self.db = MongoDBClient.get_db()
        self.users_col = self.db['users']
        self.tweets_col = self.db['tweets']

    def insert_users(self, users: List[dict]):
        if users:
            self.users_col.insert_many(users)

    def insert_user(self, user: dict) -> Any:
        return self.users_col.insert_one(user).inserted_id

    def get_user(self, user_id: int) -> Optional[dict]:
        return self.users_col.find_one({"user_id": user_id})

    def update_user(self, user_id: int, updates: dict):
        return self.users_col.update_one({"user_id": user_id}, {"$set": updates})

    def delete_user(self, user_id: int):
        return self.users_col.delete_one({"user_id": user_id})

    def insert_tweets(self, tweets: List[dict]):
        if tweets:
            self.tweets_col.insert_many(tweets)

    def insert_tweet(self, tweet: dict) -> Any:
        return self.tweets_col.insert_one(tweet).inserted_id

    def get_tweet(self, tweet_id: int) -> Optional[dict]:
        return self.tweets_col.find_one({"tweet_id": tweet_id})

    def update_tweet(self, tweet_id: int, updates: dict):
        return self.tweets_col.update_one({"tweet_id": tweet_id}, {"$set": updates})

    def delete_tweet(self, tweet_id: int):
        return self.tweets_col.delete_one({"tweet_id": tweet_id})

    def clear_collections(self):
        self.users_col.drop()
        self.tweets_col.drop()

    def get_all_users(self) -> List[dict]:
        return list(self.users_col.find({}))

    def get_all_tweets(self) -> List[dict]:
        return list(self.tweets_col.find({}))

    def count_users(self) -> int:
        return self.users_col.count_documents({})

    def count_tweets(self) -> int:
        return self.tweets_col.count_documents({})

    def count_distinct_hashtags(self) -> int:
        pipeline = [
            {"$unwind": "$hashtags"},
            {"$group": {"_id": "$hashtags"}},
            {"$count": "total"}
        ]
        result = list(self.tweets_col.aggregate(pipeline))
        return result[0]["total"] if result else 0

    def count_tweets_with_hashtag(self, hashtag: str) -> int:
        return self.tweets_col.count_documents({"hashtags": hashtag})

    def count_users_with_hashtag(self, hashtag: str) -> int:
        return len(self.tweets_col.distinct("user_id", {"hashtags": hashtag}))

    def get_users_with_hashtag(self, hashtag: str) -> List[dict]:
        user_ids = self.tweets_col.distinct("user_id", {"hashtags": hashtag})
        return list(self.users_col.find({"user_id": {"$in": user_ids}}))

    def get_reply_tweets(self) -> List[dict]:
        return list(self.tweets_col.find({"in_reply_to_tweet_id": {"$ne": None}}))

    def get_top_10_tweets_by_likes(self) -> List[dict]:
        return list(self.tweets_col.find(
            {}, {"tweet_id": 1, "text": 1, "favorite_count": 1, "user_id": 1, "_id": 0}
        ).sort("favorite_count", -1).limit(10))

    def get_top_10_hashtags(self) -> List[dict]:
        pipeline = [
            {"$unwind": "$hashtags"},
            {"$group": {"_id": "$hashtags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
            {"$project": {"hashtag": "$_id", "count": 1, "_id": 0}}
        ]
        return list(self.tweets_col.aggregate(pipeline))

    def get_max_user_id(self) -> int:
        user = list(self.users_col.find({}, {"user_id": 1}).sort("user_id", -1).limit(1))
        return user[0]["user_id"] if user and "user_id" in user[0] else 0

    def get_max_tweet_id(self) -> int:
        tweet = list(self.tweets_col.find({}, {"tweet_id": 1}).sort("tweet_id", -1).limit(1))
        return tweet[0]["tweet_id"] if tweet and "tweet_id" in tweet[0] else 0
