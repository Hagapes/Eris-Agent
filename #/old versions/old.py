from google.generativeai import configure as AIconfigure, GenerativeModel
import json, time
from subprocess import run as system, PIPE as SPIPE
from os import chdir, listdir, makedirs, getcwd
from os import environ, startfile
from os.path import exists, dirname
from google.generativeai.types.generation_types import StopCandidateException
from google.api_core.exceptions import ResourceExhausted
from rich.markdown import Markdown
from rich import print
import io

import requests
import subprocess
import sys
import importlib.util
from rich.markdown import Markdown
from rich import print

class PyGenerator:
    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept": "/",
            "Accept-Encoding": "identifier",
        }
        self.URL = "https://smartcodewriter.com"
    
    def ask(self, prompt):
        payload = {
            "action": "generate_python_code",
            "question": prompt,
            "special_instruction": ""
        }

        response = requests.post(self.URL + "/wp-admin/admin-ajax.php", headers=self.headers, data=payload)

        if response.status_code != 200:
            raise Exception(f"Request error: Anormal status code: {response.status_code}")

        if '' not in response.text:
            return f"python" + response.text + ""
        return response.text

    def exec(code):
        buffer = io.StringIO()
        ogstdout = sys.stdout
        try:
            sys.stdout = buffer
            exec(code)
        finally:
            sys.stdout = ogstdout
        return buffer.getvalue()

    def install_module(self, lib):
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", lib], check=True)
        except subprocess.CalledProcessError as e:
            raise ImportError(f"Couldn't install the required library {lib}. Error: {str(e)}")

    def run(self, code):
        for line in code.split('\n'):
            if 'import' in line:
                parsedLine = line.split()
                lib = parsedLine[1]

                if importlib.util.find_spec(lib) is None:
                    print(f"Module {lib} not found, attempting to install.")
                    self.install_module(lib)
        
        return self.exec(code.replace("python", "").replace("```", ""))

class Assistant:
    def __init__(self):
        AIconfigure(api_key=environ.get("GOOGLE_API_KEY"))
        model = GenerativeModel('gemini-1.5-flash', system_instruction = """
You are a command-line assistant capable of generating and executing Python scripts or Windows batch commands in JSON format. The user provides a description of the desired action, and you respond with a JSON object adhering to the following structure:

- **commands**: A list of commands formatted as Python strings that can be executed using `subprocess.run`. These can include:
    - Windows batch commands.
    - General CMD commands, including any installed CLI tools (e.g., `chocolatey`, `git`, etc.).
    - Python code generation and execution using the `pygen.py` system for script generation.
- **type**: A string representing the operation type (e.g., "writeInFile", "changeFile", "runPython").
- **content**: Required if **type** is "writeInFile" or "runPython", consisting of:
    - **path**: The file path where content will be written (for file operations).
    - **fileContent**: The content that will be written to the specified file.
    - **pythonPrompt**: The prompt that will be used to generate the Python code which will be run.

**SYNTAX RULES**:
1. All paths should escape backslashes (`C:\\\\` instead of `C:\\`).
2. All keys and strings should be enclosed in double quotes.
3. Use **writeInFile** for writing to files instead of `echo` to ensure better file management, including automatic file creation if it doesn't exist.

**Contextual Information**:
- The current directory structure, available from a `dirContent` call, will inform the responses for path and file selection.

**Custom Commands**:
- `open`: Opens the specified or current directory in Windows Explorer. If a path is provided as an argument, it will open the specified path (e.g., `open C:\\path\\to\\directory`).

**Callback Mechanism**:
- If additional information or command output is required, include a **callback** key (boolean: true or false). When **true**, the commands will be executed and the result will be returned for further processing.

**Command Format**:
- Booleans should be in JSON format.
- Avoid adding extra arguments to `cd` commands.

**Operation Types**:
1. "writeInFile" - To write content into files. This will overwrite existing data (future versions may support appending).
2. "runPython" - To generate and execute Python code using `pygen.py`. This type will generate Python scripts based on your needings.

**Response Schema**:
- For commands involving file operations or more complex actions:

  {
      "commands": [list of commands], # can be empty if no batch/Python commands are needed
      "callback": true/false,
      "type": "operation_type",
      "content": {
          "path": "file_path", # If running writeInFile
          "fileContent": "content_to_write", # If running writeInFile
          "pythonPrompt": "prompt_to_python_ai"  # If running Python code
      }
  }

- For simpler batch or Python commands:

  {
      "commands": [list of commands],
      "callback": true/false
  }
"""
)
        self.chat = model.start_chat(history=[])
        environ["GRPC_VERBOSITY"] = "ERROR"
        environ["GLOG_minloglevel"] = "2"
        self.pygen = PyGenerator()

    def _runPython(self, prompt: str):
        code = self.pygen.ask(prompt)
        if not code: 
            raise Exception("Error in python generator: No output returned.")

        md = Markdown(code)
        print("Results: ")
        print(md)

        ask = input("[bold white]Do you want to run the script? (Y/N)")
        if ask not in ['sim', 's', 'y', 'yes']:
            print("[bold red]Aborting task...[/]")
            return False

        return self.pygen.run(code)

    def _handleCommands(self, call, stdout=False):
        run_history = ""
        strdout = ""
        if 'type' in call:
            if call['type'] == 'writeInFile':
                if 'fileContent' not in call['content'] or 'path' not in call['content']:
                    print(call)
                    raise Exception("Missing content or path in writeInFile command.")
                path = call['content']['path']
                content = call['content']['fileContent']
                self._editFile(content, path)
                run_history += f'File "{path}" was edited successfully.\n'
            elif call['type'] == 'runPython':
                if 'pythonCode' not in call['content']:
                    print(call)
                    raise Exception("Missing pythonPrompt in runPython command.")
                prov = self._runPython(call['content']['pythonPrompt'])
                if not prov: return False
                run_history += f'Python code was executed successfully.\n'
                strdout += prov + '\n'

        for command in call['commands']:
            run_history += (command + '\n')
            if command.startswith('cd '):
                new_dir = command[3:].replace('"', '')
                try:
                    chdir(new_dir)
                    time.sleep(1)
                    continue
                except FileNotFoundError:
                    run_history += f"- Error: {new_dir} doesn't exist. (raw command: {command})\n"
                    continue
            elif command.startswith('mkdir '):
                mkd = command[6:].replace('"', '')
                makedirs(mkd, exist_ok=True)
                time.sleep(1)
                continue
            elif command.startswith('open'):
                resource = command[5:].replace('"', '').strip()
                if resource:
                    try:
                        startfile(resource)
                    except FileNotFoundError:
                        run_history += f"- Error: {resource} doesn't exist. (raw command: {command})\n"
                startfile(getcwd())
                time.sleep(1)
                continue
            if not stdout:
                system(command, shell=True, stdout=SPIPE, stderr=SPIPE)
            else:
                result = system(command, shell=True, capture_output=True, text=True)
                if result.stdout: strdout += result.stdout + '\n'
            if not command.startswith('echo'): time.sleep(1)
        if not stdout: return run_history
        elif stdout: return run_history, strdout

    def _editFile(self, content, path):
        path = path.strip('"')

        directory = dirname(path)

        if not exists(directory):
            makedirs(directory, exist_ok=True)

        try:
            with open(path, 'w') as f:
                f.write(content)
        except PermissionError:
            print(f"Permission denied when trying to write to {path}.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def _send(self, prompt):
        for i in range(5):
            try: 
                response = self.chat.send_message(prompt)
                break
            except StopCandidateException:
                if i == 4:
                    print("Tries exceeded. Exiting...")
                    exit()
                print("Candidate error, trying again...")
            except ResourceExhausted:
                if i == 4:
                    print("Tries exceeded. Exiting...")
                    exit()
                print("API is overloaded. Retrying in 10 seconds...")
                time.sleep(10)
        return response

    def batchAsk(self, prompt):
        dir_content = listdir() if listdir() else None
        batchPrompt = f"""User Prompt: "{prompt}"
Current Directory Content: {dir_content}
Current Directory Path: {getcwd()}"""

        response = self._send(batchPrompt)

        try: clean = json.loads(response.text)
        except: clean = self._clean(response.text)
        run_history = "```batch\n"

        if 'callback' in clean:
            cb = 0
            while clean.get('callback', False):
                # print("Response before handling callbacks:", clean)
                if cb > 5: 
                    run_history += "Callback limit reached (5/5). Exiting..."
                    break
                cb += 1
                leg, cbstr = self._handleCommands(clean, True)
                run_history += ("Callback history: \n" + leg + '\n\n-----------------------------------\n\n')
                if cbstr: 
                    response = self._send(f"SYSTEM RETURN: Callback from your last request (feel free to callback again if you still need more info or some error occurred): {cbstr}\nIncase of updates on the current directory: {getcwd()}\n")
                else:
                    break

                try: 
                    clean = json.loads(response.text)
                except: 
                    clean = self._clean(response.text)

                if 'callback' not in clean or not clean.get('callback', False):
                    break

        prov = self._handleCommands(clean)
        if not prov: return False
        run_history += prov
        return run_history

    def _clean(self, text):
        start_idx = text.find('{')
        if start_idx == -1:
            print(f"Raw response: {text}")
            raise ValueError("No valid JSON found in the response.")

        brace_count = 0
        for idx in range(start_idx, len(text)):
            if text[idx] == '{':
                brace_count += 1
            elif text[idx] == '}':
                brace_count -= 1

            if brace_count == 0:
                json_string = text[start_idx:idx + 1]
                break
        else:
            print(f"Raw response: {text}")
            raise ValueError("No valid JSON found in the response.")

        try:
            return json.loads(json_string)
        except json.decoder.JSONDecodeError:
            print(f"An error occurred while parsing the JSON string: {json_string}")
            raise

if __name__ == "__main__":
    assistant = Assistant()
    while True:
        user = input("Prompt: ")
        print("[bold white]Executing command...")
        run_history = assistant.batchAsk(prompt=user)
        if not run_history: continue
        if run_history:
            print("\nRun history:")
            print(Markdown(run_history))
        print("\n[bold white]Command executed successfully.")