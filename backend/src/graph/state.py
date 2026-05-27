import operator
from threading import local
from typing import Annotated, Optional, List, Dict, Any, Optional, TypedDict

# Define the structure of a compliance issue
class ComplianceIssue(TypedDict):
    category: str
    description: str
    severity: str   
    timestamp: Optional[str]
    

# define the global graph state
# this defines the state that will be passed between the different nodes in the graph of agentic workflow
class VideoAuditState(TypedDict):
    video_url: str
    video_id: str

    local_filepath: Optional[str]
    video_metadata: Dict[str, Any]
    transcript: Optional[str]
    ocr_text: List[str]

    # stores list of all violations found by AI
    compliance_results: Annotated[List[ComplianceIssue], operator.add]
    
    final_status: str
    final_report: str

    #system observability
    #errors: API timeout, system level errors
    #list of system level crashes
    errors: Annotated[List[str], operator.add]