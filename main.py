# import libs
from google.generativeai import configure as AIconfigure, GenerativeModel
from google.generativeai.types.generation_types import StopCandidateException
from google.api_core.exceptions import ResourceExhausted
from os import environ, getcwd, listdir, makedirs
import json
from os.path import exists
from rich import print

# import local modules
from commands.find import find
from commands.generators import PythonCodeGenerator
from commands.search import Search

# main class
class SuAGENT:
    # initializes
    def __init__(self):
        # initializes gemini
        AIconfigure(api_key=environ.get("GOOGLE_API_KEY"))
        with open('systemrules.txt', 'r') as f:
            self.baseSYSTEM = f.read()
        model = GenerativeModel('gemini-1.5-flash', system_instruction=self.baseSYSTEM)
        self.chat = model.start_chat(history=[])
        environ["GRPC_VERBOSITY"] = "ERROR"
        environ["GLOG_minloglevel"] = "2"
        self.gen = PythonCodeGenerator()
        self.search = Search()

    def _returnToAI(self, content: str):
        self.think(
            f"SYSTEM RETURN: Your last request returned the following responses: \n{content}"
        )

    def _process(self, response: str):
        rtrnSequence = ""
        for rqsts in response['requests']:
            if rqsts['type'] == 'code_execution':
                print(f"[bold yellow][INFORMATION][/] 🧑‍💻 Generating code...")
                rtrnSequence += str(self.gen.inject(rqsts['parameters']['prompt'], 'execute')) + '\n'
            elif rqsts['type'] == 'search':
                print(f"[bold yellow][INFORMATION][/] 🚢 Navigating on the web...")
                results = self.search.search(rqsts['parameters']['query'])
                rtrnSequence += 'Response from search command:' + results + '\n'

            elif rqsts['type'] == 'find':
                print(f"[bold yellow][INFORMATION][/] 🔎 Searching for file '{rqsts['parameters']['file_name']}'...")
                rtrnSequence += 'Response from find command:' + str(find(rqsts['parameters']['file_name'])) + '\n'
            elif rqsts['type'] == 'writeInFile':
                makedirs(rqsts['parameters']['path'], exist_ok=True)

                print(f"[bold yellow][INFORMATION][/] 📝 Writing in file '{rqsts['parameters']['path']}'...")

                if exists(rqsts['parameters']['path']):
                    ask = input(f"The file at {rqsts['parameters']['path']} already exists. Do you want to overwrite it? (Y/N) ")
                    if ask.lower() not in ['y', 'yes']:
                        continue
                with open(rqsts['parameters']['path'], 'w') as f:
                    f.write(rqsts['parameters']['text'])
                rtrnSequence += f"File written at {rqsts['parameters']['path']}" + '\n'
            elif rqsts['type'] == 'simple_print':
                print(f"[bold green][A.I.][/]: {rqsts['parameters']['text']}")

        if rtrnSequence != "":
            self._returnToAI(rtrnSequence)

    def think(self, prompt: str):
        additionalInfo = (
            "Before recieving the user prompt, here is some additional info about the current enviroment: \n"
            f"Current path: {getcwd()}"
            f"Current directory content: {listdir()}"
            "Context: Use the 'current directory content' list to know what the user is speaking about, if he asks to change a filed name 'filename' but doesnt specify the extension, use the content as your resource to know what file he is talking about."
        )

        raw = self.chat.send_message(additionalInfo + prompt)
        try: resources = json.loads(raw.text.replace('```json', '').replace('```', ''))
        except: raise Exception(f"An error occurred while parsing the JSON string: {raw}")

        self._process(resources)

        print(resources)

if __name__ == "__main__":
    agent = SuAGENT()
    while True:
        prompt = input(">> ")
        agent.think(prompt)