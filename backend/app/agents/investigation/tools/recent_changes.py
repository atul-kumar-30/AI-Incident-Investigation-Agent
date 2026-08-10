import os
import subprocess
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.tools.base import BaseTool
import app.db.session
from app.models.repository import Repository
from app.models.incident import incident_repositories

class RecentChangesTool(BaseTool):
    name = "recent_changes"
    description = "Inspect recent Git commits and file changes in repositories associated with the incident."
    input_schema = {
        "type": "object",
        "properties": {
            "incident_id": {"type": "string"},
            "repository_ids": {"type": "array", "items": {"type": "string"}},
            "since_time": {"type": "string"},
            "until_time": {"type": "string"},
            "max_commits": {"type": "integer"},
            "path_filter": {"type": "string"},
            "query": {"type": "string"}
        },
        "required": ["incident_id", "repository_ids"]
    }

    async def _verify_repositories(self, db: AsyncSession, incident_id: str, repository_ids: List[str]) -> bool:
        """Verify that all requested repositories are associated with the incident."""
        if not repository_ids:
            return True
            
        result = await db.execute(
            select(incident_repositories.c.repository_id)
            .where(incident_repositories.c.incident_id == incident_id)
        )
        allowed_repo_ids = {row[0] for row in result.all()}
        
        for r_id in repository_ids:
            if r_id not in allowed_repo_ids:
                return False
        return True
        
    async def _get_all_incident_repositories(self, db: AsyncSession, incident_id: str) -> List[str]:
        result = await db.execute(
            select(incident_repositories.c.repository_id)
            .where(incident_repositories.c.incident_id == incident_id)
        )
        return [row[0] for row in result.all()]

    def _execute_git_command(self, cwd: str, args: List[str]) -> str:
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "Error: Git command timed out."
        except subprocess.CalledProcessError as e:
            return f"Error: Git command failed. {e.stderr}"

    async def execute(self, **kwargs) -> Dict[str, Any]:
        incident_id = kwargs.get("incident_id")
        repository_ids = kwargs.get("repository_ids", [])
        since_time = kwargs.get("since_time")
        until_time = kwargs.get("until_time")
        max_commits = kwargs.get("max_commits", 10)
        path_filter = kwargs.get("path_filter")
        query = kwargs.get("query")

        async with app.db.session.AsyncSessionLocal() as db:
            is_valid = await self._verify_repositories(db, incident_id, repository_ids)
            if not is_valid:
                return {"error": "One or more repository IDs are not associated with this incident."}

            if not repository_ids:
                repository_ids = await self._get_all_incident_repositories(db, incident_id)
                if not repository_ids:
                    return {"error": "No repositories associated with this incident."}

            result = await db.execute(
                select(Repository).where(Repository.id.in_(repository_ids))
            )
            repos = result.scalars().all()

            results = []
            for repo in repos:
                repo_path = os.path.abspath(repo.source_location)
                
                if not os.path.isdir(os.path.join(repo_path, ".git")):
                    results.append({"repository_id": repo.id, "error": "Not a Git repository."})
                    continue
                
                git_args = ["log", f"-n{max_commits}", "--pretty=format:%H|%aI|%an|%s", "--name-status"]
                
                if since_time:
                    git_args.append(f"--since={since_time}")
                if until_time:
                    git_args.append(f"--until={until_time}")
                if query:
                    git_args.append(f"--grep={query}")
                if path_filter:
                    git_args.extend(["--", path_filter])
                    
                log_output = self._execute_git_command(repo_path, git_args)
                
                if log_output.startswith("Error"):
                    results.append({"repository_id": repo.id, "error": log_output})
                    continue
                    
                commits = self._parse_git_log(log_output, repo_path)
                results.append({"repository_id": repo.id, "commits": commits})
                
            return {"results": results}

    def _parse_git_log(self, log_output: str, repo_path: str) -> List[Dict[str, Any]]:
        commits = []
        current_commit = None
        
        for line in log_output.strip().split("\n"):
            if not line.strip():
                continue
                
            if "|" in line and len(line.split("|")) == 4:
                hash_val, time_val, author_val, msg_val = line.split("|", 3)
                current_commit = {
                    "commit_hash": hash_val,
                    "timestamp": time_val,
                    "author": author_val,
                    "message": msg_val,
                    "changed_files": []
                }
                commits.append(current_commit)
            elif current_commit and "\t" in line:
                status, filepath = line.split("\t", 1)
                
                diff_snippet = ""
                if status != "D": 
                    diff_actual = self._execute_git_command(
                        repo_path,
                        ["show", current_commit['commit_hash'], "--", filepath]
                    )
                    lines = diff_actual.split("\n")
                    if len(lines) > 500:
                        diff_snippet = "\n".join(lines[:500]) + "\n... [diff truncated]"
                    else:
                        diff_snippet = diff_actual
                        
                current_commit["changed_files"].append({
                    "path": filepath,
                    "status": status,
                    "diff_snippet": diff_snippet
                })
                
        return commits
