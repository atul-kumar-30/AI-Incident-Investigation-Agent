from app.agents.investigation.state import InvestigationState

async def finalize(state: InvestigationState) -> dict:
    """Finalize the investigation run."""
    errors = state.get("errors", [])
    hypotheses = state.get("hypotheses", [])
    
    if errors:
        status = "FAILED"
        summary = f"Investigation failed: {'; '.join(errors)}"
    elif not hypotheses:
        status = "COMPLETED"
        summary = "Evidence collection and preliminary analysis completed. Current evidence was insufficient to generate strongly supported hypotheses."
    else:
        status = "COMPLETED"
        leading_hypothesis = hypotheses[0]
        
        summary = (
            f"Preliminary hypothesis analysis completed.\n\n"
            f"{len(hypotheses)} candidate explanations were generated from the collected evidence.\n\n"
            f"The strongest currently supported hypothesis is that {leading_hypothesis.get('description', '').lower()}\n\n"
            f"This ranking reflects current evidence support only.\n"
            f"No hypothesis has yet been formally verified or rejected."
        )
        
    return {
        "current_step": "finalize",
        "status": status,
        "summary": summary
    }
