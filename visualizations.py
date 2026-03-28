import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pyvis.network import Network
import os
import logging
from services_mongo import MongoService
from services_neo4j import Neo4jService
from utils import setup_logging

logger = logging.getLogger(__name__)

class VisualizationService:
    def __init__(self, mongo_service: MongoService, neo4j_service: Neo4jService):
        self.mongo_service = mongo_service
        self.neo4j_service = neo4j_service
        self.output_dir = "outputs"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")

    def generate_mongo_charts(self):
        logger.info("Generating MongoDB analytics charts...")
        
        hashtags_data = self.mongo_service.get_top_10_hashtags()
        if hashtags_data:
            df_tags = pd.DataFrame(hashtags_data)
            plt.figure(figsize=(10, 6))
            sns.barplot(x='count', y='hashtag', data=df_tags, palette='viridis')
            plt.title('Top 10 Most Popular Hashtags')
            plt.xlabel('Number of Tweets')
            plt.ylabel('Hashtags')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "top_10_hashtags.png"))
            plt.close()
            logger.info("Saved top_10_hashtags.png")

        tweets_data = self.mongo_service.get_top_10_tweets_by_likes()
        if tweets_data:
            df_tweets = pd.DataFrame(tweets_data)
            df_tweets['short_text'] = df_tweets['text'].apply(lambda x: (x[:40] + '...') if len(x) > 40 else x)
            plt.figure(figsize=(10, 6))
            sns.barplot(x='favorite_count', y='short_text', data=df_tweets, palette='magma')
            plt.title('Top 10 Most Liked Tweets')
            plt.xlabel('Favorite Count')
            plt.ylabel('Tweet Content')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "top_10_tweets_likes.png"))
            plt.close()
            logger.info("Saved top_10_tweets_likes.png")

        users = self.mongo_service.get_all_users()
        if users:
            df_users = pd.DataFrame(users)
            role_counts = df_users['role'].value_counts()
            plt.figure(figsize=(8, 8))
            plt.pie(role_counts, labels=role_counts.index, autopct='%1.1f%%', colors=sns.color_palette('pastel'))
            plt.title('Distribution of User Roles')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "user_roles_distribution.png"))
            plt.close()
            logger.info("Saved user_roles_distribution.png")

    def generate_neo4j_graph(self):
        logger.info("Generating Neo4j Ego Network for MilanoOps...")
        graph_data = self.neo4j_service.get_milano_ops_ego_network()
        
        if not graph_data["nodes"]:
            logger.warning("No data found for MilanoOps ego network.")
            return

        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", notebook=False)
        
        for node in graph_data["nodes"]:
            net.add_node(node['id'], label=node['label'], title=f"Type: {node['type']}", color=node['color'])
        
        for edge in graph_data["edges"]:
            net.add_edge(edge['from'], edge['to'], label=edge['label'], color="#aaaaaa")
        
        net.toggle_physics(True)
        
        output_path = os.path.join(self.output_dir, "milano_ops_ego_network.html")
        net.write_html(output_path)
        logger.info(f"Saved Neo4j graph visualization to {output_path}")

if __name__ == "__main__":
    setup_logging()
    m = MongoService()
    n = Neo4jService()
    viz = VisualizationService(m, n)
    viz.generate_mongo_charts()
    viz.generate_neo4j_graph()