'''
This module defines the workflow DAG: directed acyclic graph of nodes that defines the workflow of the compliance QA pipeline. 
Each node takes in the state, performs a specific function and outputs the updated state which is passed on to the next node in the workflow.

START -> index_video_node -> audio_content_node -> END
'''

from langgraph.graph import StateGraph, END  # pyright: ignore[reportMissingImports]
from backend.src.graph.state import VideoAuditState
from backend.src.graph.nodes import index_video_node, audit_content_node

def create_graph():
    '''
    Constructs & compiles the langraph workflow
    Returns:
    Compiled Graph: runnable graph object that can be executed with an initial state
    '''

    #initialize graph with starting state schema
    workflow = StateGraph(VideoAuditState)
    #add nodes to the graph
    workflow.add_node("indexer", index_video_node)
    workflow.add_node("auditor", audit_content_node)
    # define the entry point: indexer
    workflow.set_entry_point("indexer")

    #add edges to the graph
    workflow.add_edge("indexer", "auditor")
    workflow.add_edge("auditor", END)
    #compile the graph
    app = workflow.compile()   # ← compile here
    #expose the compiled graph app for execution with an initial state
    return app

app = create_graph()           # ← this line is fine as-is
