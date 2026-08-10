import asyncio
import uuid
import random
from datetime import datetime, timedelta, timezone
from app.db.session import AsyncSessionLocal
from app.models.incident import Incident
from app.schemas.log import LogEntryCreate
from app.services.log_service import LogService

async def main():
    async with AsyncSessionLocal() as session:
        # Get the first incident, or create one if none exists
        from sqlalchemy import select
        result = await session.execute(select(Incident).limit(1))
        incident = result.scalar_one_or_none()
        
        if not incident:
            print("No incident found. Creating one...")
            incident = Incident(
                id=str(uuid.uuid4()),
                title="Test Incident for Phase 3",
                description="Database timeout issues in payment gateway",
                severity="HIGH",
                source="MANUAL"
            )
            session.add(incident)
            await session.commit()
            
        incident_id = incident.id
        print(f"Seeding logs for incident: {incident_id}")
        
        service = LogService(session)
        logs = []
        
        base_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        services = ["auth-service", "payment-gateway", "user-profile", "notification-service"]
        
        # 1. Normal traffic (noise)
        for i in range(150):
            logs.append(LogEntryCreate(
                timestamp=base_time + timedelta(seconds=i*5),
                level="INFO",
                service=random.choice(services),
                message=f"Handled request successfully {uuid.uuid4().hex[:8]}",
                endpoint=random.choice(["/api/v1/health", "/api/v1/users", "/metrics"]),
                http_status=200,
                trace_id=uuid.uuid4().hex
            ))
            
        # 2. Database Timeout issue leading to 500s in payment-gateway
        for i in range(20):
            trace_id = uuid.uuid4().hex
            time_offset = base_time + timedelta(minutes=15, seconds=i*30)
            
            # DB timeout log
            logs.append(LogEntryCreate(
                timestamp=time_offset,
                level="ERROR",
                service="payment-gateway",
                message="Connection pool exhausted: database timeout while acquiring connection",
                endpoint=None,
                http_status=None,
                trace_id=trace_id
            ))
            
            # API failure log shortly after
            logs.append(LogEntryCreate(
                timestamp=time_offset + timedelta(milliseconds=500),
                level="WARN",
                service="payment-gateway",
                message="Failed to process transaction: internal error",
                endpoint="/api/v1/checkout",
                http_status=500,
                trace_id=trace_id
            ))
            
        # 3. Related auth-service failures due to same DB pool (as requested in prompt "auth-service" /login 500 error patterns)
        for i in range(15):
            trace_id = uuid.uuid4().hex
            time_offset = base_time + timedelta(minutes=16, seconds=i*45)
            
            logs.append(LogEntryCreate(
                timestamp=time_offset,
                level="ERROR",
                service="auth-service",
                message="Database query timeout during token validation",
                endpoint=None,
                http_status=None,
                trace_id=trace_id
            ))
            
            logs.append(LogEntryCreate(
                timestamp=time_offset + timedelta(milliseconds=300),
                level="ERROR",
                service="auth-service",
                message="Authentication failed: backend error",
                endpoint="/login",
                http_status=500,
                trace_id=trace_id
            ))

        # Shuffle logs to make it realistic
        random.shuffle(logs)
        
        print(f"Ingesting {len(logs)} logs...")
        await service.bulk_ingest(incident_id, logs)
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
