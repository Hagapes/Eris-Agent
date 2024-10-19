# import libs
from google.generativeai import configure as AIconfigure, GenerativeModel
from google.generativeai.types.generation_types import StopCandidateException
from google.api_core.exceptions import ResourceExhausted
from os import environ, getcwd, listdir, makedirs, chdir
import json
from os.path import exists
from rich import print
from rich.markdown import Markdown
from rich.console import Console
from subprocess import run as system
from os import popen, startfile
import time
from datetime import date

# import local modules
from commands.find import find
from commands.generators import PythonCodeGenerator
from commands.search import Search

# main class
class ErisAgent:
    def __init__(self, debug: bool = False):
        AIconfigure(api_key=environ.get("GOOGLE_API_KEY"))
        with open('systemrules.txt', 'r') as f:
            self.baseSYSTEM = f.read()
        model = GenerativeModel('gemini-1.5-flash', system_instruction=self.baseSYSTEM)
        self.chat = model.start_chat(history=[])
        environ["GRPC_VERBOSITY"] = "ERROR"
        environ["GLOG_minloglevel"] = "2"
        self.gen = PythonCodeGenerator()
        self.search = Search()
        self.console = Console()
        self.debug = debug

    def _returnToAI(self, content: str):
        self.think(
            f"SYSTEM RETURN: Your last request returned the following responses: \n{content}"
        )

    def _process(self, response: str):
        rtrnSequence = ""
        for rqsts in response['requests']:
            if rqsts['type'] == 'code_execution':
                print(f"\n[bold yellow][INFORMATION][/] 🧑‍💻 Generating code...")
                rtrnSequence += str(self.gen.inject(rqsts['parameters']['prompt'], 'execute')) + '\n'
            elif rqsts['type'] == 'code_store':
                print(f"\n[bold yellow][INFORMATION][/] 🧑‍💻 Generating code...")
                rtrnSequence += self.gen.inject(rqsts['parameters']['prompt'], 'store') 
            elif rqsts['type'] == 'search':
                print(f"\n[bold yellow][INFORMATION][/] 🚢 Navigating on the web...")
                results = self.search.search(rqsts['parameters']['query'])
                rtrnSequence += 'Response from search command:' + results + '\n'

            elif rqsts['type'] == 'find':
                print(f"\n[bold yellow][INFORMATION][/] 🔎 Searching for file '{rqsts['parameters']['file_name']}'...")
                rtrnSequence += 'Response from find command:' + str(find(rqsts['parameters']['file_name'])) + '\n'
            elif rqsts['type'] == 'write_file':
                try: makedirs(rqsts['parameters']['path'], exist_ok=True)
                except FileExistsError: pass

                print(f"\n[bold yellow][INFORMATION][/] 📝 Writing in file '{rqsts['parameters']['path']}'...")

                if exists(rqsts['parameters']['path']):
                    ask = input(f"The file at {rqsts['parameters']['path']} already exists. Do you want to overwrite it? (Y/N) ")
                    if ask.lower() not in ['y', 'yes']:
                        continue
                with open(rqsts['parameters']['path'], 'w') as f:
                    f.write(rqsts['parameters']['text'])
                rtrnSequence += f"File written at {rqsts['parameters']['path']}" + '\n'
            elif rqsts['type'] == 'simple_print':
                print("[bold green][A.I.][/]: ", end="")
                print(Markdown(f"{rqsts['parameters']['text']}\n"), end="\n")
            elif rqsts['type'] == 'question':
                while True:
                    answer = self.console.input(f"[bold green][A.I.][/]: {rqsts['parameters']['text']} ")
                    if answer.lower().strip() == "exit":
                        rtrnSequence += f"User did not wanted to answer the question {rqsts['parameters']['text']}.\n"
                        break
                    if not answer: continue
                    rtrnSequence += answer
                    break
            elif rqsts['type'] == 'terminal_run':
                commands = rqsts['parameters']['commands']
                stdout = ""
                for command in commands:
                    cmd = system(command, shell=True, capture_output=True, text=True)
                    if cmd.stdout: stdout += cmd.stdout + '\n'
                    if cmd.stderr: stdout += cmd.stderr + '\n'

                if stdout != "": rtrnSequence += stdout
            elif rqsts['type'] == 'open':
                try: startfile(rqsts['parameters']['path'])
                except Exception as e: rtrnSequence += f"Error while starting file: {str(e)}"
            elif rqsts['type'] == 'read_file':
                print(f"\n[bold yellow][INFORMATION][/] 📝 Reading from file '{rqsts['parameters']['path']}'...")
                try:
                    with open(rqsts['parameters']['path'], 'r') as f:
                        rtrnSequence += f"The content of the file that you requested is (remember to print if the user asked/logically want you to print): \n{f.read()}"
                except Exception as e:
                    rtrnSequence += f"Error while reading file: {str(e)}"
            elif rqsts['type'] == 'change_wdir':
                try: chdir(rqsts['parameters']['path'])
                except Exception as e: rtrnSequence += f"Error while changing directory: {str(e)}"
            elif rqsts['type'] == 'makedirs':
                try: makedirs(rqsts['parameters']['path'], exist_ok=True)
                except Exception as e: rtrnSequence += f"Error while creating directory(ies): {str(e)}"

            else: raise Exception(f"Invalid request type: {rqsts['type']}")


        if rtrnSequence != "":
            self._returnToAI(rtrnSequence)

    def think(self, prompt: str):
        additionalInfo = (
            "THIS IS PART OF THE SYSTEM: Before recieving the user prompt, here is some additional info about the current enviroment: \n"
            f"Current path: {getcwd()}"
            f"Current directory content: {listdir()}"
            f"Current task list: {popen('tasklist').read()}"
            f"Current date: {date.today()}"
            f"Current timestamp: {time.time()}"
            "Context: Use the 'current directory content' list to know what the user is speaking about, if he asks to change a filed name 'filename' but doesnt specify the extension, use the content as your resource to know what file he is talking about."
        )

        for i in range(10):
            if i == 9:
                raise ResourceExhausted("Max tries exceeded. Exiting...")

            try:
                raw = self.chat.send_message(additionalInfo + f"Now, here is the user prompt: {prompt}")
                break
            except ResourceExhausted:
                print("API is overloaded. Retrying in 10 seconds...") 
                time.sleep(10)
            except StopCandidateException:
                print("Candidate error, trying again...")
                

        try: resources = json.loads(raw.text.replace('```json', '').replace('```', ''))
        except: raise Exception(f"An error occurred while parsing the JSON string: {raw}")

        self._process(resources)

        if self.debug: print(resources)

if __name__ == "__main__":
    agent = ErisAgent(debug=False)
    while True:
        prompt = input(f"{getcwd()} >> ")
        if not prompt: continue
        agent.think(prompt)