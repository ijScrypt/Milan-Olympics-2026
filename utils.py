import logging
import sys
from datetime import datetime
from typing import Any, Dict, List

def setup_logging():
    """
    Centralized logging configuration.
    Sets up a consistent format and stdout stream handler.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def format_mongo_for_neo4j(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitizes MongoDB documents for Neo4j ingestion.
    Converts ObjectId to string and datetime to ISO string.
    """
    sanitized = []
    for doc in documents:
        # Use a copy to avoid mutating the original documents if needed
        d = doc.copy()
        if '_id' in d:
            d['_id'] = str(d['_id'])
        
        # Convert all datetime objects to ISO strings
        for key, value in d.items():
            if isinstance(value, datetime):
                d[key] = value.isoformat()
        
        sanitized.append(d)
    return sanitized