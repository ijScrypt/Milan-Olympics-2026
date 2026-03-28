import logging
import sys
from datetime import datetime
from typing import Any, Dict, List

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def format_mongo_for_neo4j(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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