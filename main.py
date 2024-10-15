"""will write the workflow first"""

# import libs
from google.generativeai import configure as AIconfigure, GenerativeModel
from google.generativeai.types.generation_types import StopCandidateException
from google.api_core.exceptions import ResourceExhausted
from os import environ

# import local modules
from commands.find import find

# main class
class SuAGENT:
    # initializes
    def __init__(self):

        # initializes gemini
        AIconfigure(api_key=environ.get("GOOGLE_API_KEY"))
        model = GenerativeModel('gemini-1.5-flash')

        self.jsonSchema = """{
            "request": {
                "type": "string",                # Type of command (e.g., "code_execution", "file_operation", "search")
                "parameters": {                  # Optional parameters based on the type
                    "python_prompt": "string",   # Python code prompt to send to generation AI (if type is "code_execution")
                    "file_path": "string",       # Path to a file (if type is "file_operation")
                    "file_content": "string",    # Content to write to the file (if type is "file_operation")
                }
            }
        }"""

# unused (atm)
#                    "search_query": "string",    # Search terms (if type is "search")
#                    "search_type": "string",     # Type of search (e.g., "by_name", "by_extension", "by_content") - if type is "search"

        # creates a temporary chat for context windows
        self.chat = model.start_chat(history=[])
        environ["GRPC_VERBOSITY"] = "ERROR"
        environ["GLOG_minloglevel"] = "2"

    def think(self, prompt: str):
        pass