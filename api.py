"""
Flask API backend for the Milano 2026 Dashboard.
Exposes MongoDB data and query execution endpoints.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from services_mongo import MongoService
from services_neo4j import Neo4jService
from seed import SeedService
import json
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
CORS(app)

mongo = MongoService()
neo4j = Neo4jService()


class JSONEncoder(json.JSONEncoder):
    """Custom encoder to handle ObjectId and datetime."""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        return super().default(o)


app.json_encoder = JSONEncoder


def serialize(doc):
    """Convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize(d) for d in doc]
    if isinstance(doc, dict):
        return {k: (str(v) if isinstance(v, ObjectId) else v.isoformat() if hasattr(v, 'isoformat') else v)
                for k, v in doc.items()}
    return doc


# ─── KPI Endpoints ───────────────────────────────────────────────────────────

@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    """Return all KPIs for the dashboard header."""
    return jsonify({
        'total_users': mongo.count_users(),
        'total_tweets': mongo.count_tweets(),
        'distinct_hashtags': mongo.count_distinct_hashtags(),
        'tweets_milano2026': mongo.count_tweets_with_hashtag('milano2026'),
        'users_milano2026': mongo.count_users_with_hashtag('milano2026'),
        'reply_tweets': len(mongo.get_reply_tweets()),
    })


@app.route('/api/kpis/neo4j', methods=['GET'])
def get_neo4j_kpis():
    """Return all KPIs for the dashboard header."""
    return jsonify(neo4j.get_kpis())


# ─── Data Endpoints ──────────────────────────────────────────────────────────

@app.route('/api/users', methods=['GET'])
def get_users():
    users = mongo.get_all_users()
    return jsonify(serialize(users))


@app.route('/api/tweets', methods=['GET'])
def get_tweets():
    tweets = mongo.get_all_tweets()
    return jsonify(serialize(tweets))


@app.route('/api/top-hashtags', methods=['GET'])
def get_top_hashtags():
    return jsonify(serialize(mongo.get_top_10_hashtags()))


@app.route('/api/top-tweets', methods=['GET'])
def get_top_tweets():
    return jsonify(serialize(mongo.get_top_10_tweets_by_likes()))


@app.route('/api/user-roles', methods=['GET'])
def get_user_roles():
    users = mongo.get_all_users()
    roles = {}
    for u in users:
        r = u.get('role', 'unknown')
        roles[r] = roles.get(r, 0) + 1
    return jsonify(roles)


@app.route('/api/tweet-timeline', methods=['GET'])
def get_tweets_timeline():
    """Aggregate tweet counts by date for timeline chart."""
    pipeline = [
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    result = list(mongo.tweets_col.aggregate(pipeline))
    return jsonify([{"date": r["_id"], "count": r["count"]} for r in result])


# ─── Query Execution ─────────────────────────────────────────────────────────

AVAILABLE_QUERIES = {
    "q1_count_users": {
        "label": "1. Nombre d'utilisateurs",
        "description": "Compte le nombre total d'utilisateurs enregistrés",
        "db": "mongodb"
    },
    "q2_count_tweets": {
        "label": "2. Nombre de tweets",
        "description": "Compte le nombre total de tweets dans la base",
        "db": "mongodb"
    },
    "q3_count_distinct_hashtags": {
        "label": "3. Nombre de hashtags distincts",
        "description": "Compte le nombre de hashtags uniques utilisés",
        "db": "mongodb"
    },
    "q4_count_tweets_hashtag": {
        "label": "4. Tweets contenant un hashtag (paramètre)",
        "description": "Nombre de tweets contenant le hashtag sélectionné",
        "db": "mongodb"
    },
    "q5_distinct_users_milano2026": {
        "label": "5. Utilisateurs distincts ayant utilisé #milano2026",
        "description": "Nombre d'utilisateurs distincts ayant utilisé le hashtag sélectionné",
        "db": "mongodb"
    },
    "q6_reply_tweets": {
        "label": "6. Tweets qui sont des réponses",
        "description": "Liste des tweets qui sont des réponses à d'autres tweets",
        "db": "mongodb"
    },
    "q7_neo4j_milano_ops_followers": {
        "label": "7. Followers de MilanoOps",
        "description": "Liste des utilisateurs qui suivent MilanoOps",
        "db": "neo4j"
    },
    "q8_neo4j_milano_ops_following": {
        "label": "8. Utilisateurs suivis par MilanoOps",
        "description": "Liste des utilisateurs que MilanoOps suit",
        "db": "neo4j"
    },
    "q9_neo4j_mutual_follows": {
        "label": "9. Relations réciproques avec MilanoOps",
        "description": "Utilisateurs qui se suivent mutuellement avec MilanoOps",
        "db": "neo4j"
    },
    "q10_neo4j_hubs": {
        "label": "10. Utilisateurs avec >10 followers",
        "description": "Utilisateurs avec plus de 10 followers",
        "db": "neo4j"
    },
    "q11_neo4j_active_followers": {
        "label": "11. Utilisateurs qui suivent >5 personnes",
        "description": "Utilisateurs qui suivent plus de 5 personnes",
        "db": "neo4j"
    },
    "q12_top_10_tweets_likes": {
        "label": "12. Top 10 tweets les plus populaires",
        "description": "Les 10 tweets avec le plus de favoris",
        "db": "mongodb"
    },
    "q13_top_10_hashtags": {
        "label": "13. Top 10 hashtags les plus populaires",
        "description": "Les 10 hashtags les plus fréquents",
        "db": "mongodb"
    },
    "q14_neo4j_conversation_roots": {
        "label": "14. Tweets qui initient une discussion",
        "description": "Tweets qui sont le début d'un fil de discussion",
        "db": "neo4j"
    },
    "q15_neo4j_longest_discussion": {
        "label": "15. La plus longue discussion",
        "description": "Chaîne de réponses la plus longue",
        "db": "neo4j"
    },
    "q16_neo4j_thread_extents": {
        "label": "16. Début et fin de chaque conversation",
        "description": "Pour chaque conversation : premier et dernier tweet",
        "db": "neo4j"
    }
}


@app.route('/api/queries', methods=['GET'])
def list_queries():
    """Return available queries."""
    return jsonify(AVAILABLE_QUERIES)


@app.route('/api/execute', methods=['POST'])
def execute_query():
    """Execute a selected query and return results."""
    data = request.get_json()
    query_id = data.get('query_id')
    param = data.get('param')
    target_db = data.get('target_db')

    if query_id not in AVAILABLE_QUERIES:
        return jsonify({'error': 'Requête inconnue'}), 400

    q_info = AVAILABLE_QUERIES.get(query_id)

    # If the requested target_db doesn't match the query's native db, return no_data
    if target_db and target_db != q_info.get("db"):
        return jsonify({"result": {"no_data": True}, "query": q_info, "target_db": target_db})

    result = None
    try:
        # MongoDB
        if query_id == "q1_count_users":
            result = {"count": mongo.count_users()}
        elif query_id == "q2_count_tweets":
            result = {"count": mongo.count_tweets()}
        elif query_id == "q3_count_distinct_hashtags":
            result = {"count": mongo.count_distinct_hashtags()}
        elif query_id == "q4_count_tweets_hashtag":
            hashtag = param if param else "milano2026"
            hashtag = hashtag.lstrip('#')
            result = {"count": mongo.count_tweets_with_hashtag(hashtag)}
        elif query_id == "q5_distinct_users_milano2026":
            hashtag = param if param else "milano2026"
            hashtag = hashtag.lstrip('#')
            users = mongo.get_users_with_hashtag(hashtag)
            result = {"count": len(users), "data": serialize(users[:50])}
        elif query_id == "q6_reply_tweets":
            replies = mongo.get_reply_tweets()
            result = {"count": len(replies), "data": serialize(replies[:50])}
        elif query_id == "q12_top_10_tweets_likes":
            result = {"data": serialize(mongo.get_top_10_tweets_by_likes())}
        elif query_id == "q13_top_10_hashtags":
            result = {"data": serialize(mongo.get_top_10_hashtags())}
        # Neo4j
        elif query_id == "q7_neo4j_milano_ops_followers":
            result = {"data": neo4j.get_milano_ops_followers()}
        elif query_id == "q8_neo4j_milano_ops_following":
            result = {"data": neo4j.get_milano_ops_following()}
        elif query_id == "q9_neo4j_mutual_follows":
            result = {"data": neo4j.get_mutual_follows_with("MilanoOps")}
        elif query_id == "q10_neo4j_hubs":
            result = {"data": neo4j.get_hubs()}
        elif query_id == "q11_neo4j_active_followers":
            result = {"data": neo4j.get_active_followers()}
        elif query_id == "q14_neo4j_conversation_roots":
            result = {"data": neo4j.get_conversation_roots()}
        elif query_id == "q15_neo4j_longest_discussion":
            discussion = neo4j.get_longest_discussion()
            if discussion:
                result = {"count": discussion["length"], "data": serialize(discussion["tweets"])}
            else:
                result = {"count": 0, "data": []}
        elif query_id == "q16_neo4j_thread_extents":
            result = {"data": neo4j.get_thread_extents()}

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'query': AVAILABLE_QUERIES[query_id],
        'result': result
    })


# --- Seed Endpoint -----------------------------------------------------------

@app.route('/api/seed', methods=['POST'])
def seed_data():
    """Re-seed the database."""
    try:
        SeedService(mongo).execute_seed(30, 200, 0.35)
        return jsonify({'message': 'Base de données re-seedée avec succès', 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- CRUD Users -------------------------------------------------------------

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('role') or not data.get('country'):
        return jsonify({"success": False, "error": "Missing required fields: username, role, country"}), 400
    
    if data['role'] not in ['staff', 'bénévole', 'journaliste', 'fan']:
        return jsonify({"success": False, "error": "Invalid role"}), 400
        
    if 'user_id' not in data:
        data['user_id'] = mongo.get_max_user_id() + 1
        
    if 'created_at' not in data:
        from datetime import datetime
        data['created_at'] = datetime.utcnow().isoformat()
        
    inserted_id = mongo.insert_user(data)
    return jsonify({"success": True, "data": {"user_id": data['user_id'], "_id": str(inserted_id)}}), 201


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user_endpoint(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
        
    if 'role' in data and data['role'] not in ['staff', 'bénévole', 'journaliste', 'fan']:
        return jsonify({"success": False, "error": "Invalid role"}), 400
        
    res = mongo.update_user(user_id, data)
    if res.matched_count == 0:
        return jsonify({"success": False, "error": "User not found"}), 404
        
    return jsonify({"success": True, "data": {"updated_count": res.modified_count}})


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user_endpoint(user_id):
    res = mongo.delete_user(user_id)
    if res.deleted_count == 0:
        return jsonify({"success": False, "error": "User not found"}), 404
    return jsonify({"success": True, "data": {"deleted_count": res.deleted_count}})


# --- CRUD Tweets ------------------------------------------------------------

@app.route('/api/tweets', methods=['POST'])
def create_tweet():
    data = request.get_json()
    if not data or 'user_id' not in data or 'text' not in data:
        return jsonify({"success": False, "error": "Missing required fields: user_id, text"}), 400
        
    if 'hashtags' not in data or not isinstance(data['hashtags'], list):
        data['hashtags'] = []
        
    if 'favorite_count' not in data:
        data['favorite_count'] = 0
        
    if 'tweet_id' not in data:
        data['tweet_id'] = mongo.get_max_tweet_id() + 1
        
    if 'created_at' not in data:
        data['created_at'] = datetime.now().isoformat()
        
    inserted_id = mongo.insert_tweet(data)
    return jsonify({"success": True, "data": {"tweet_id": data['tweet_id'], "_id": str(inserted_id)}}), 201


@app.route('/api/tweets/<int:tweet_id>', methods=['PUT'])
def update_tweet_endpoint(tweet_id):
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
        
    if 'hashtags' in data and not isinstance(data['hashtags'], list):
        # If it's a string, try to convert it (should be handled by JS but safety first)
        if isinstance(data['hashtags'], str):
             data['hashtags'] = [h.strip() for h in data['hashtags'].split(',')]
        else:
             return jsonify({"success": False, "error": "hashtags must be a list"}), 400
        
    res = mongo.update_tweet(tweet_id, data)
    if res.matched_count == 0:
        return jsonify({"success": False, "error": "Tweet not found"}), 404
        
    return jsonify({"success": True, "data": {"updated_count": res.modified_count}})


@app.route('/api/tweets/<int:tweet_id>', methods=['DELETE'])
def delete_tweet_endpoint(tweet_id):
    res = mongo.delete_tweet(tweet_id)
    if res.deleted_count == 0:
        return jsonify({"success": False, "error": "Tweet not found"}), 404
    return jsonify({"success": True, "data": {"deleted_count": res.deleted_count}})
if __name__ == '__main__':
    # Auto-seed if database is empty
    if mongo.count_users() == 0:
        print("[INIT] Base de données vide détectée - seeding automatique...")
        SeedService(mongo).execute_seed(30, 200, 0.35)
        print(f"[INIT] [OK] {mongo.count_users()} utilisateurs, {mongo.count_tweets()} tweets créés.")
    else:
        print(f"[INIT] Base existante : {mongo.count_users()} utilisateurs, {mongo.count_tweets()} tweets.")

    app.run(debug=True, port=5000)
