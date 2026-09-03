from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, or_, and_, cast, String, func
from typing import List, Optional, Tuple
from datetime import datetime
from app.models.log import LogEntry
from app.schemas.log import LogEntryCreate

class LogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_insert(self, incident_id: str, logs: List[LogEntryCreate]) -> List[LogEntry]:
        db_logs = []
        for log_in in logs:
            db_log = LogEntry(
                incident_id=incident_id,
                **log_in.model_dump()
            )
            self.session.add(db_log)
            db_logs.append(db_log)
            
        await self.session.commit()
        for db_log in db_logs:
            await self.session.refresh(db_log)
        return db_logs

    async def search(
        self,
        incident_id: str,
        query: Optional[str] = None,
        levels: Optional[List[str]] = None,
        services: Optional[List[str]] = None,
        endpoint: Optional[str] = None,
        http_status: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[int, List[LogEntry]]:
        
        stmt = select(LogEntry).where(or_(LogEntry.incident_id == incident_id, LogEntry.incident_id.is_(None)))
        
        if query:
            # Simple case-insensitive search in message for Phase 3
            stmt = stmt.where(LogEntry.message.ilike(f"%{query}%"))
            
        if levels:
            stmt = stmt.where(cast(LogEntry.level, String).in_([l.upper() for l in levels]))
            
        if services:
            stmt = stmt.where(LogEntry.service.in_(services))
            
        if endpoint:
            stmt = stmt.where(LogEntry.endpoint == endpoint)
            
        if http_status is not None:
            stmt = stmt.where(LogEntry.http_status == http_status)
            
        if start_time:
            stmt = stmt.where(LogEntry.timestamp >= start_time)
            
        if end_time:
            stmt = stmt.where(LogEntry.timestamp <= end_time)
            
        # Get total count (simple approach for now)
        # Note: For production, we'd use func.count(), but for Phase 3 this is okay with limited result sets
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total_matches = total_result.scalar() or 0
        
        # Add order by and limits
        stmt = stmt.order_by(desc(LogEntry.timestamp)).offset(offset).limit(limit)
        
        result = await self.session.execute(stmt)
        logs = list(result.scalars().all())
        
        return total_matches, logs
