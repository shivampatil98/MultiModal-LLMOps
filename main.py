from dotenv import load_dotenv
load_dotenv(override=True)

import uuid
import json
import logging
from pprint import pprint
from backend.src.graph.workflow import app

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger("ComplianceQAPipeline")

def run_cli_simulation():
    '''
    Simulates the workflow execution with a sample video URL input. This can be used for testing and debugging the workflow logic.
    '''
    session_id = str(uuid.uuid4())  # Generate a unique session ID for this run
    logger.info(f"Starting audit session: {session_id}")

    inital_inputs = {
        "video_url": "https://youtu.be/7QLzzSml07Y",  # Sample YouTube video URL for testing
        "video_id": f"vid_{session_id[:8]}",  # Optional video ID input, if not provided a random one will be generated
        "compliance_results": [],  # Initialize compliance results as an empty list
        "errors": []  # Initialize errors list to store intermediate errors from each node
    }

    print("\n-----Initalizing Workflow with Inputs:-----\n")
    # json.dumps() converts python dict to formatted JSON string
    print(f"Input Payload: {json.dumps(inital_inputs, indent=2)}")

    # Run the workflow with the initial inputs
    try:
        # app.invoke() runs the workflow defined in the graph with the provided inputs and returns the final state after execution.
        #   The final state will contain all the data accumulated and processed through the different nodes in the workflow, including any compliance issues found and the final audit report.
        final_state = app.invoke(inital_inputs)
        print("\n-----Workflow Execution Completed---\n")

        print("\n Compliance audit report ==")
        print(f"Video ID: {final_state.get('video_id')}")
        print(f"Final Status: {final_state.get('final_status')}")
        results = final_state.get("compliance_results", [])

        if results:
            for issue in results:
                print(f"- Category: {issue['category']}, Severity: {issue['severity']}, issue: {issue['description']}")
        else:
            print("No compliance issues found.")

    except Exception as e:
        logger.error(f"Error during workflow execution: {str(e)}")
        raise e

if __name__ == "__main__":
    run_cli_simulation()
