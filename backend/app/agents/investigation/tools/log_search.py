from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.tools.base import BaseTool
import app.db.session
from app.repositories.log_repository import LogRepository
from datetime import datetime

class LogSearchInput(BaseModel):
    incident_id: str
    query: Optional[str] = None
    levels: Optional[List[str]] = None
    services: Optional[List[str]] = None
    endpoint: Optional[str] = None
    http_status: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: Optional[int] = 25

class LogSearchTool(BaseTool):
    name = "log_search"
    description = "Search application logs associated with the current incident using time ranges, services, log levels, endpoints, HTTP status codes and keywords. Use this to find runtime evidence."
    input_schema = {
        "type": "object",
        "properties": {
            "incident_id": {"type": "string", "description": "The ID of the incident to analyze"},
            "query": {"type": "string", "description": "Case-insensitive keyword search in log messages"},
            "levels": {"type": "array", "items": {"type": "string"}, "description": "List of log levels (e.g., ['ERROR', 'WARN'])"},
            "services": {"type": "array", "items": {"type": "string"}, "description": "List of services to filter by (e.g., ['auth-service'])"},
            "endpoint": {"type": "string", "description": "Exact match for endpoint (e.g., '/login')"},
            "http_status": {"type": "integer", "description": "Exact match for HTTP status code (e.g., 500)"},
            "limit": {"type": "integer", "description": "Maximum number of logs to return. Default is 25, max 100."}
        },
        "required": ["incident_id"]
    }

    async def execute(self, incident_id: str, **kwargs) -> Dict[str, Any]:
        async with app.db.session.AsyncSessionLocal() as session:
            repo = LogRepository(session)
            
            query = kwargs.get("query")
            levels = kwargs.get("levels")
            services = kwargs.get("services")
            endpoint = kwargs.get("endpoint")
            http_status = kwargs.get("http_status")
            start_time = kwargs.get("start_time")
            end_time = kwargs.get("end_time")
            limit = kwargs.get("limit", 25)
            
            if limit > 100:
                limit = 100
                
            total_matches, logs = await repo.search(
                incident_id=incident_id,
                query=query,
                levels=levels,
                services=services,
                endpoint=endpoint,
                http_status=http_status,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
            # Deterministic summarization based on returned logs
            pattern_counts = {}
            for log in logs:
                # Basic pattern extraction using HTTP status and endpoint or message snippet
                pattern = None
                if log.http_status and log.endpoint:
                    pattern = f"HTTP {log.http_status} {log.endpoint}"
                else:
                    # Truncate message for a simple pattern string (just for basic grouping)
                    pattern = (log.message[:50] + '...') if len(log.message) > 50 else log.message
                
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            # Sort patterns by frequency
            sorted_patterns = [{"pattern": p, "count": c} for p, c in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
            
            services_found = list(set([log.service for log in logs]))
            
            result = {
                "query_summary": {
                    "query": query,
                    "levels": levels,
                    "services": services,
                    "endpoint": endpoint,
                    "http_status": http_status,
                },
                "total_matches": total_matches,
                "returned_count": len(logs),
                "truncated": total_matches > len(logs),
                "extracted_patterns": sorted_patterns,
                "services": services_found,
                "logs": [
                    {
                        "timestamp": log.timestamp.isoformat(),
                        "level": log.level.value,
                        "service": log.service,
                        "message": log.message,
                        "endpoint": log.endpoint,
                        "http_status": log.http_status,
                        "trace_id": log.trace_id,
                        "id": log.id
                    } for log in logs
                ]
            }
            
            return result
