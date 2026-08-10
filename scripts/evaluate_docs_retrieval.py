import asyncio
import os
import sys

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db.session import AsyncSessionLocal
from app.services.document_service import DocumentService
from app.services.retrieval_service import RetrievalService
from app.models.document import Document
from app.models.repository import Repository
from app.models.incident import Incident

async def evaluate():
    print("Initializing services...")
    doc_service = DocumentService()
    retrieval_service = RetrievalService()

    async with AsyncSessionLocal() as db:
        print("Seeding demo documents...")
        await doc_service.ingest_demo_documents(db)
        
        # Test Queries mapping to expected document filename
        test_cases = [
            ("connection pool exhaustion", "db_pool_exhaustion.md"),
            ("HTTP 502 /login failures", "auth_5xx.md"),
            ("How many connections are in the auth service pool?", "auth_architecture.md"),
            ("retries for email notification", "email_noise.md")
        ]

        hits_at_1 = 0
        hits_at_3 = 0
        mrr_sum = 0.0

        print(f"\nEvaluating {len(test_cases)} test queries...\n")
        for query, expected_filename in test_cases:
            results = await retrieval_service.hybrid_search(
                db=db,
                query=query,
                incident_id=None, # Search all
                top_k=5
            )
            
            rank = None
            for i, res in enumerate(results):
                # Retrieve the document from db to get filename/source_name
                if res["document_type"] in ["RUNBOOK", "TROUBLESHOOTING", "ARCHITECTURE", "GENERAL"]:
                    # We stored source_name as the filename
                    # Note: We didn't fetch source_name in the hybrid_search projection, but let's see if title or chunk content gives a hint
                    pass
                
            # Actually, our retrieval returns title and document_id. Let's look up source_name.
            doc_filenames = []
            for res in results:
                doc = await db.get(Document, res["document_id"])
                doc_filenames.append(doc.source_name)
                
            for i, filename in enumerate(doc_filenames):
                if filename == expected_filename:
                    rank = i + 1
                    break
                    
            if rank:
                if rank == 1:
                    hits_at_1 += 1
                if rank <= 3:
                    hits_at_3 += 1
                mrr_sum += 1.0 / rank
                print(f"✅ Query: '{query}' -> Found expected document at Rank {rank}")
            else:
                print(f"❌ Query: '{query}' -> Expected '{expected_filename}', but not found in top 5.")
                print("Returned:", doc_filenames)

        mrr = mrr_sum / len(test_cases)
        
        print("\n--- Evaluation Results ---")
        print(f"Total Queries: {len(test_cases)}")
        print(f"Hit@1: {hits_at_1} ({hits_at_1/len(test_cases)*100:.1f}%)")
        print(f"Hit@3: {hits_at_3} ({hits_at_3/len(test_cases)*100:.1f}%)")
        print(f"MRR:   {mrr:.3f}")

if __name__ == "__main__":
    asyncio.run(evaluate())
