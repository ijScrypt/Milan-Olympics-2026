from neo4j_client import Neo4jClient
from services_mongo import MongoService
from datetime import datetime


def format_mongo_for_neo4j(documents):
    sanitized = []
    for doc in documents:
        d = doc.copy()
        if '_id' in d:
            d['_id'] = str(d['_id'])
        for key, value in d.items():
            if isinstance(value, datetime):
                d[key] = value.isoformat()
        sanitized.append(d)
    return sanitized

class Neo4jService:
    def __init__(self):
        self.driver = Neo4jClient.get_driver()

    def _run_read_query(self, query: str, **parameters):
        with self.driver.session() as session:
            result = session.run(query, **parameters)
            return [dict(record) for record in result]

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def create_constraints(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE")
            session.run("CREATE CONSTRAINT tweet_id_unique IF NOT EXISTS FOR (t:Tweet) REQUIRE t.tweet_id IS UNIQUE")

    def import_from_mongo(self, mongo_service: MongoService):
        self.clear_database()
        self.create_constraints()

        users = format_mongo_for_neo4j(mongo_service.get_all_users())
        tweets = format_mongo_for_neo4j(mongo_service.get_all_tweets())

        with self.driver.session() as session:
            session.run("""
            UNWIND $users AS u
            MERGE (user:User {user_id: u.user_id})
            SET user.username = u.username,
                user.role = u.role,
                user.country = u.country
            """, users=users)

            session.run("""
            UNWIND $tweets AS t
            MERGE (tweet:Tweet {tweet_id: t.tweet_id})
            SET tweet.text = t.text,
                tweet.favorite_count = t.favorite_count,
                tweet.created_at = t.created_at
            """, tweets=tweets)

            session.run("""
            UNWIND $tweets AS t
            MATCH (u:User {user_id: t.user_id})
            MATCH (tweet:Tweet {tweet_id: t.tweet_id})
            MERGE (u)-[:AUTHORED]->(tweet)
            """, tweets=tweets)

            replies = [t for t in tweets if t.get("in_reply_to_tweet_id") is not None]
            session.run("""
            UNWIND $replies AS r
            MATCH (reply:Tweet {tweet_id: r.tweet_id})
            MATCH (parent:Tweet {tweet_id: r.in_reply_to_tweet_id})
            MERGE (reply)-[:REPLY_TO]->(parent)
            """, replies=replies)

            session.run("""
            MATCH (u1:User), (u2:User)
            WHERE u1 <> u2 AND rand() < 0.1
            MERGE (u1)-[:FOLLOWS]->(u2)
            """)

            session.run("""
            MATCH (u:User), (t:Tweet)
            WHERE NOT (u)-[:AUTHORED]->(t) AND rand() < 0.05
            MERGE (u)-[:RETWEETS]->(t)
            """)

    def get_milano_ops_followers(self):
        results = self._run_read_query("""
            MATCH (follower:User)-[:FOLLOWS]->(ops:User {username: "MilanoOps"})
            RETURN follower.username AS username
        """)
        return [r["username"] for r in results]

    def get_milano_ops_following(self):
        results = self._run_read_query("""
            MATCH (ops:User {username: "MilanoOps"})-[:FOLLOWS]->(followed:User)
            RETURN followed.username AS username
        """)
        return [r["username"] for r in results]

    def get_mutual_follows_with(self, username="MilanoOps"):
        results = self._run_read_query("""
            MATCH (u1:User {username: $username})-[:FOLLOWS]->(u2:User),
                  (u2)-[:FOLLOWS]->(u1)
            RETURN u2.username AS username
        """, username=username)
        return [r["username"] for r in results]

    def get_hubs(self, threshold=10):
        return self._run_read_query("""
            MATCH (u:User)<-[r:FOLLOWS]-(:User)
            WITH u, count(r) AS followers_count
            WHERE followers_count > $threshold
            RETURN u.username AS username, followers_count
            ORDER BY followers_count DESC
        """, threshold=threshold)

    def get_active_followers(self, threshold=5):
        return self._run_read_query("""
            MATCH (u:User)-[r:FOLLOWS]->(:User)
            WITH u, count(r) AS following_count
            WHERE following_count > $threshold
            RETURN u.username AS username, following_count
            ORDER BY following_count DESC
        """, threshold=threshold)

    def get_conversation_roots(self):
        return self._run_read_query("""
            MATCH (root:Tweet)<-[:REPLY_TO]-(:Tweet)
            WHERE NOT (root)-[:REPLY_TO]->(:Tweet)
            RETURN DISTINCT root.tweet_id AS tweet_id, root.text AS text
        """)

    def get_longest_discussion(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH p = (leaf:Tweet)-[:REPLY_TO*]->(root:Tweet)
                WHERE NOT (root)-[:REPLY_TO]->()
                RETURN nodes(p) AS discussion, length(p) AS length
                ORDER BY length DESC
                LIMIT 1
            """)
            record = result.single()
            if record:
                return {
                    "length": record["length"],
                    "tweets": [dict(node) for node in record["discussion"]]
                }
            return None

    def get_thread_extents(self):
        return self._run_read_query("""
            MATCH (root:Tweet)
            WHERE NOT (root)-[:REPLY_TO]->()
            MATCH p = (leaf:Tweet)-[:REPLY_TO*0..]->(root)
            WHERE NOT ()-[:REPLY_TO]->(leaf)
            WITH root, leaf, length(p) AS depth
            ORDER BY root.tweet_id, depth DESC
            WITH root, collect({id: leaf.tweet_id, text: leaf.text})[0] AS last_reply
            RETURN root.tweet_id AS first_tweet_id, root.text AS first_tweet_text,
                   last_reply.id AS last_tweet_id, last_reply.text AS last_tweet_text
        """)

    def get_kpis(self):
        query = """
        CALL {
            MATCH (n:User) RETURN count(n) AS user_count
        }
        CALL {
            MATCH (n:Tweet) RETURN count(n) AS tweet_count
        }
        CALL {
            MATCH ()-[r:FOLLOWS]->() RETURN count(r) AS follows_count
        }
        CALL {
            MATCH ()-[r:AUTHORED]->() RETURN count(r) AS authored_count
        }
        CALL {
            MATCH ()-[r:RETWEETS]->() RETURN count(r) AS retweets_count
        }
        CALL {
            MATCH ()-[r:REPLY_TO]->() RETURN count(r) AS replies_count
        }
        RETURN user_count, tweet_count, follows_count, authored_count, retweets_count, replies_count
        """
        result = self._run_read_query(query)
        if not result:
            return {}

        data = result[0]
        return {
            "total_users": data.get("user_count", 0),
            "total_tweets": data.get("tweet_count", 0),
            "total_follows": data.get("follows_count", 0),
            "total_authored": data.get("authored_count", 0),
            "total_retweets": data.get("retweets_count", 0),
            "total_replies": data.get("replies_count", 0),
            "total_relationships": sum(data.get(f"{rel}_count", 0) for rel in ["follows", "authored", "retweets", "replies"])
        }

    def get_milano_ops_ego_network(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:User {username: "MilanoOps"})-[r]-(neighbor)
                RETURN m, r, neighbor
            """)
            nodes = {}
            edges = []

            for record in result:
                m_node = record["m"]
                neighbor_node = record["neighbor"]
                rel = record["r"]
                
                m_id = m_node['user_id']
                if m_id not in nodes:
                    nodes[m_id] = {
                        "id": m_id, 
                        "label": m_node['username'], 
                        "group": "center", 
                        "color": "#f59e0b",
                        "size": 30
                    }

                neighbor_id = neighbor_node.get('user_id') or neighbor_node.get('tweet_id')
                if neighbor_id and neighbor_id not in nodes:
                    if 'username' in neighbor_node:
                        group = "user"
                        color = "#6366f1"
                    else:
                        group = "tweet"
                        color = "#10b981"
                    
                    label = neighbor_node.get('username') or f"Tweet #{str(neighbor_id)[:8]}..."
                    nodes[neighbor_id] = {
                        "id": neighbor_id, 
                        "label": label, 
                        "group": group, 
                        "color": color
                    }
                
                if rel.start_node['user_id'] == m_id:
                    source_id, target_id = m_id, neighbor_id
                else:
                    source_id, target_id = neighbor_id, m_id
                
                edges.append({"from": source_id, "to": target_id, "label": rel.type})

            return {"nodes": list(nodes.values()), "edges": edges}

    def get_all_relationships_graph(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n1)-[r]->(n2)
                RETURN n1, r, n2
                LIMIT 100
            """)
            nodes = {}
            edges = []
            table_data = []

            for record in result:
                n1_node = record["n1"]
                n2_node = record["n2"]
                rel = record["r"]
                
                n1_id = n1_node.get('user_id') or n1_node.get('tweet_id')
                n1_label = n1_node.get('username') or f"Tweet #{str(n1_id)[:8]}..."
                
                if n1_id and n1_id not in nodes:
                    nodes[n1_id] = {
                        "id": n1_id, 
                        "label": n1_label, 
                        "group": "user" if 'username' in n1_node else "tweet", 
                        "color": "#6366f1" if 'username' in n1_node else "#10b981"
                    }

                n2_id = n2_node.get('user_id') or n2_node.get('tweet_id')
                n2_label = n2_node.get('username') or f"Tweet #{str(n2_id)[:8]}..."
                
                if n2_id and n2_id not in nodes:
                    nodes[n2_id] = {
                        "id": n2_id, 
                        "label": n2_label, 
                        "group": "user" if 'username' in n2_node else "tweet", 
                        "color": "#6366f1" if 'username' in n2_node else "#10b981"
                    }
                
                edges.append({"from": n1_id, "to": n2_id, "label": rel.type})
                
                table_data.append({
                    "Source": n1_label,
                    "Type": rel.type,
                    "Cible": n2_label
                })

            return {"nodes": list(nodes.values()), "edges": edges, "data": table_data}