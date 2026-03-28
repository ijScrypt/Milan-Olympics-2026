import random
from datetime import datetime, timedelta
from faker import Faker
from services_mongo import MongoService

fake = Faker('fr_FR')

class SeedService:
    def __init__(self, mongo_service: MongoService):
        self.mongo_service = mongo_service

    def generate_users(self, num_users: int) -> list:
        users_list = []
        base_created_at = datetime(2026, 3, 18, 12, 0)
        milano_ops = {
            "user_id": 1, 
            "username": "MilanoOps", 
            "role": "staff", 
            "country": "IT",
            "created_at": base_created_at
        }
        users_list.append(milano_ops)
        roles = ["staff", "bénévole", "journaliste", "fan"]
        countries = ["FR", "IT", "DE", "US", "JP", "TN", "ES"]
        for i in range(2, num_users + 1):
            user = {
                "user_id": i, 
                "username": fake.user_name(), 
                "role": random.choice(roles),
                "country": random.choice(countries),
                "created_at": base_created_at + timedelta(minutes=random.randint(10, 2000))
            }
            users_list.append(user)
        return users_list

    def generate_tweets(self, num_tweets: int, users: list, reply_ratio: float) -> list:
        tweets_list = []
        base_time = datetime(2026, 1, 1, 12, 0)
        hashtag_pool = ["milano2026", "transport", "sécurité", "météo", "cérémonie", "stade"]
        for i in range(1, num_tweets + 1):
            base_time += timedelta(minutes=random.randint(5, 60))
            author = random.choice(users)
            num_hashtags = random.randint(1, 3)
            selected_hashtags = []
            if random.random() < 0.7:
                selected_hashtags.append("milano2026")
            while len(selected_hashtags) < num_hashtags:
                candidate = random.choice(hashtag_pool)
                if candidate not in selected_hashtags:
                    selected_hashtags.append(candidate)
            reply_id = None
            if random.random() < reply_ratio and len(tweets_list) > 0:
                reply_id = random.choice(tweets_list)["tweet_id"]
            tweet = {
                "tweet_id": i, "user_id": author["user_id"], "text": fake.sentence(nb_words=10),
                "hashtags": selected_hashtags, "created_at": base_time,
                "favorite_count": random.randint(0, 500), "in_reply_to_tweet_id": reply_id
            }
            tweets_list.append(tweet)
        return tweets_list

    def execute_seed(self, num_users: int, num_tweets: int, reply_ratio: float):
        self.mongo_service.clear_collections()
        users = self.generate_users(num_users)
        self.mongo_service.insert_users(users)
        tweets = self.generate_tweets(num_tweets, users, reply_ratio)
        self.mongo_service.insert_tweets(tweets)

if __name__ == "__main__":
    service = MongoService()
    seeder = SeedService(mongo_service=service)
    seeder.execute_seed(30, 200, 0.35)
