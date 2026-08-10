import os
import hashlib
import re
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.repository import Repository, SourceFile, CodeChunk, IngestionStatus
from app.core.logging import logger

EXCLUDED_DIRS = {".git", "node_modules", "dist", "build", "coverage", "venv", ".venv", "__pycache__"}
INCLUDED_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".cpp", ".c", ".h", 
    ".cs", ".rs", ".sql", ".yml", ".yaml", ".json", ".toml", ".env.example"
}
MAX_FILE_SIZE = 1024 * 1024 * 2  # 2MB

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_symbols_python(lines: list[str], start: int) -> str | None:
    # Very basic symbol extraction for the start of a chunk
    for line in lines:
        match = re.match(r'^\s*(def|class)\s+([a-zA-Z0-9_]+)', line)
        if match:
            return match.group(2)
    return None

def extract_symbols_ts(lines: list[str], start: int) -> str | None:
    for line in lines:
        match = re.match(r'^\s*(export\s+)?(const|function|class|interface|type)\s+([a-zA-Z0-9_]+)', line)
        if match:
            return match.group(3)
    return None

def extract_symbols(lines: list[str], ext: str, start: int) -> str | None:
    if ext == ".py":
        return extract_symbols_python(lines, start)
    elif ext in {".ts", ".tsx", ".js", ".jsx"}:
        return extract_symbols_ts(lines, start)
    return None

class IndexerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def index_repository(self, repository_id: str):
        # Update status to INDEXING
        repo = await self.db.get(Repository, repository_id)
        if not repo:
            return
            
        repo.ingestion_status = IngestionStatus.INDEXING
        await self.db.commit()
        
        try:
            await self._process_directory(repo)
            
            repo.ingestion_status = IngestionStatus.READY
            repo.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to index repository {repo_id}: {e}")
            repo.ingestion_status = IngestionStatus.FAILED
            await self.db.commit()

    async def _process_directory(self, repo: Repository):
        root_path = repo.source_location
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
            
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in INCLUDED_EXTENSIONS:
                    continue
                    
                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, root_path)
                
                try:
                    size = os.path.getsize(filepath)
                    if size > MAX_FILE_SIZE:
                        continue
                        
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    content_hash = hash_content(content)
                    
                    # Check if file exists and hash matches
                    result = await self.db.execute(
                        select(SourceFile).filter_by(repository_id=repo.id, path=rel_path)
                    )
                    existing_file = result.scalars().first()
                    
                    if existing_file:
                        if existing_file.content_hash == content_hash:
                            continue # Unchanged
                        else:
                            # Delete old chunks implicitly by CASCADE or explicitly
                            await self.db.delete(existing_file)
                            await self.db.flush()
                            
                    # Insert new SourceFile
                    source_file = SourceFile(
                        repository_id=repo.id,
                        path=rel_path,
                        language=ext.strip("."),
                        size_bytes=size,
                        content_hash=content_hash,
                        indexed_at=datetime.now(timezone.utc)
                    )
                    self.db.add(source_file)
                    await self.db.flush()
                    
                    # Generate chunks
                    self._generate_chunks(source_file, content, ext)
                    
                except UnicodeDecodeError:
                    continue # Skip binary or weird encodings
                except Exception as e:
                    logger.warning(f"Failed to process file {rel_path}: {e}")
                    
        await self.db.commit()

    def _generate_chunks(self, source_file: SourceFile, content: str, ext: str):
        lines = content.split('\n')
        total_lines = len(lines)
        
        chunk_size = 100
        overlap = 20
        
        i = 0
        while i < total_lines:
            end = min(i + chunk_size, total_lines)
            chunk_lines = lines[i:end]
            chunk_content = '\n'.join(chunk_lines)
            
            symbol_name = extract_symbols(chunk_lines, ext, i)
            
            chunk = CodeChunk(
                source_file_id=source_file.id,
                start_line=i + 1,
                end_line=end,
                symbol_name=symbol_name,
                chunk_type="line_window",
                content=chunk_content,
                content_hash=hash_content(chunk_content)
            )
            self.db.add(chunk)
            
            i += (chunk_size - overlap)
