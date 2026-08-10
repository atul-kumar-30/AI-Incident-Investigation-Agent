import json
import uuid
from app.agents.investigation.state import InvestigationState

async def record_evidence(state: InvestigationState) -> dict:
    """Format tool results into evidence records."""
    tool_results = state.get("tool_results", [])
    new_evidence = []
    
    for result in tool_results:
        if result.get("status") == "COMPLETED":
            tool_name = result.get("tool_name")
            output = result.get("output", {})
            
            content = json.dumps(output, indent=2)
            if isinstance(output, dict) and "summary" in output:
                content = output.get("summary", content) + "\n\nSignals: " + json.dumps(output.get("signals", {}), indent=2)
            
            source_type = "TOOL"
            if tool_name == "log_search":
                source_type = "LOG"
            elif tool_name == "code_search":
                source_type = "CODE"
                content = f"Code Search Query: {output.get('query')}\nMatches: {output.get('returned_count')}\n\n"
                for res in output.get("results", []):
                    content += f"File: {res.get('file_path')} (Lines: {res.get('start_line')}-{res.get('end_line')})\nSnippet:\n{res.get('snippet')}\n\n"
            elif tool_name == "recent_changes":
                source_type = "GIT_CHANGE"
                content = "Recent Git Changes:\n"
                for repo_res in output.get("results", []):
                    for commit in repo_res.get("commits", []):
                        content += f"Commit: {commit.get('commit_hash')} by {commit.get('author')}\nMessage: {commit.get('message')}\n\n"
            elif tool_name == "docs_search":
                source_type = "DOCUMENT"
                content = f"Docs Search Query: {output.get('query')}\nMatches: {output.get('returned_count')}\n\n"
                for res in output.get("results", []):
                    content += f"Document: {res.get('title')} ({res.get('document_type')})\n"
                    if res.get('section_title'):
                        content += f"Section: {res.get('section_title')}\n"
                    if res.get('page_number'):
                        content += f"Page: {res.get('page_number')}\n"
                    content += f"Snippet:\n{res.get('snippet')}\n\n"
                
            evidence_item = {
                "id": str(uuid.uuid4()),
                "source_type": source_type,
                "source_name": tool_name,
                "content": content,
                "metadata": output
            }
            new_evidence.append(evidence_item)
            
    result_state = {
        "current_step": "record_evidence",
        "evidence": new_evidence,
        # Clear tool requests/results for the next iteration
        "tool_requests": [],
        "tool_results": []
    }
    
    # If we are in verification mode, update new_evidence_ids
    verification = state.get("verification", {})
    if verification and verification.get("status") == "RUNNING":
        new_verification = verification.copy()
        # Merge with existing new_evidence_ids if they exist
        existing_new = new_verification.get("new_evidence_ids", [])
        new_verification["new_evidence_ids"] = existing_new + [e["id"] for e in new_evidence]
        result_state["verification"] = new_verification
        
    return result_state
