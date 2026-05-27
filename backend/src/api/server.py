import uuid
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv(override=True)

from backend.src.api.telemetry import setup_telemetry

from backend.src.graph.workflow import app as compliance_graph

#configure logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("api-server")

app = FastAPI(title="Compliance QA API", 
              description="API for auditing video content against compliance standards.",
              version = "1.0.0"
            )

class AuditRequest(BaseModel):
    '''
    Define the expected structure of incoming API requests
    Example valid request:
    {
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "video_id": "optional_custom_id"
    }
    '''

    video_url: str

class ComplianceIssue(BaseModel):
    '''
    Define the structure of compliance issues identified in the video
    '''
    category: str
    severity: str
    description: str

class AuditResponse(BaseModel):
    session_id: str
    video_id: str
    status: str
    final_report: str
    compliance_results: List[ComplianceIssue]

# Define the main endpoint
@app.post("/audit", response_model=AuditResponse)

async def audit_video(request: AuditRequest):
    '''
    Main API endpoint to receive video audit requests. It triggers the compliance graph workflow and returns the results.
    '''
    logger.info(f"Received audit request for video: {request.video_url}")
    # Generate a unique session ID for tracking
    session_id = str(uuid.uuid4())
    video_id_short = f"vid_{session_id[:8]}"  # Generate a short unique video ID for tracking
    
    initial_inputs = {
            "video_url": request.video_url,
            "video_id": video_id_short,
            "compliance_results": [],
            "errors": []
        }
    
    try:
        # Trigger the compliance graph workflow with the provided video URL and session ID
        final_state = compliance_graph.invoke(initial_inputs)
        return AuditResponse(
            session_id=session_id,
            video_id=final_state.get("video_id"),
            status=final_state.get("final_status", "unknown"),
            final_report=final_state.get("final_report", ""),
            compliance_results=final_state.get("compliance_results", [])
        )     
    except Exception as e:
        logger.error(f"Audit failed : {str(e)}")   
        raise HTTPException(status_code=500, 
                            detail=f"Workflow execution failed: {str(e)}")
    
@app.get("/health")

def health_check():
    '''
    Simple health check endpoint to verify that the API is running
    '''
    return {"status": "ok", "version": app.version, "service": "Compliance QA API"}