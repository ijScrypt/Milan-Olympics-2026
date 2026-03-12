from app.mongo_client import get_mongo_db
from app.neo4j_client import get_neo4j_driver

def test_mongo():
    db = get_mongo_db()
    print("MongoDB OK")
    print("Base visée :", db.name)

def test_neo4j():
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("RETURN 'Neo4j OK' AS message")
        print(result.single()["message"])
    driver.close()

if __name__ == "__main__":
    test_mongo()
    test_neo4j()