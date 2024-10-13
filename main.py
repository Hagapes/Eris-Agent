import google.generativeai as genai
import json, re, time
from subprocess import run as system, PIPE as SPIPE
from os import chdir, listdir, makedirs, getcwd
from os import environ
from google.generativeai.types.generation_types import StopCandidateException
from google.api_core.exceptions import ResourceExhausted
from rich.markdown import Markdown
from rich import print

class Assistant:
    def __init__(self):
        genai.configure(api_key=environ.get("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-pro')
        self.chat = model.start_chat(history=[])
        environ["GRPC_VERBOSITY"] = "ERROR"
        environ["GLOG_minloglevel"] = "2"

    def _handleCommands(self, call, stdout=False):
        run_history = ""
        strdout = ""
        for command in call['commands']:
            run_history += (command + '\n')
            if command.startswith('cd '):
                new_dir = command[3:].replace('"', '')
                try:
                    chdir(new_dir)
                    time.sleep(1)
                    continue
                except FileNotFoundError:
                    run_history += f"[bold red]Error: {new_dir} doesn't exist. (raw command: {command})\n"
                    continue
            elif command.startswith('mkdir '):
                mkd = command[6:].replace('"', '')
                makedirs(mkd, exist_ok=True)
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
        with open(path, 'w') as f:
            f.write(content)

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
        batchPrompt = """You are a command-line assistant that generates a list of Windows batch commands based on user requests. The user will provide a prompt describing the desired action, and you will generate a dict with the following keys:

- **commands**: A list of commands in Python format that can be executed using subprocess.run. This key may be omitted for certain actions.
- **type**: A string indicating the type of operation (e.g., "writeInFile", "changeFile").
- **content**: (Required if **type** is "writeInFile") A JSON object containing two keys: 
  - **path**: The path to the file where content will be written.
  - **fileContent**: The content to be written into the file.

**SYNTAX RULES**:
- Always escape backslash characters with a backslash when it comes to paths. For example, use C:\\\\ instead of C:\\.
- Ensure all keys and strings are properly quoted using double quotes.

The user prompt will include instructions like creating folders, files, or executing other command-line tasks. You should consider the contents of the current directory provided in the variable `dirContent`, which is a list of files and folders in the user's current directory, to inform your responses.

For example, if the user says, "edit README.md and put some random things in it", you would respond with:
{
   "commands": [], 
   "callback": true, 
   "type": "writeInFile", 
   "content": {
       "path": "...\\README.md",
       "fileContent": "This is a random test content to test the file writing functionality. You can write any text in here!"
   }
}

**WARNING**: In case of writeInFile, REMEMBER to always end every dict! You've showed errors where you dont close the "content" dict.

**IMPORTANT**: If you need extra information, you can get it by adding a new key to the dict, called **callback**, which should be a boolean, either True or False. If True, the script will run the batch commands and return the stdout to you so you can continue the process or callback again to run more commands.

Feel free to callback as many times as you need to gather data; just be aware of the RPM to avoid overloads.
If the user asks to write/gather data of a file, use the **type** command and set **callback** as true. It should return the content of the file as stdout.

**NOTE**: Use '\\' to escape double quotes in your prompt to avoid errors in the dict parser. Some commands like 'more' are not processed; instead, use echo to answer.
**OBS**: Use JSON to write booleans, because of the parser being a JSON parser. Do not add extra arguments to the 'cd' command; the code translates it to feed the chdir function.

Avaliable types:
    "writeInFile" - to edit files (this overwrites data, appending data will be added in later versions)

Use this JSON schema:

Format 1: {'commands': list[str], 'callback': bool, 'type': str, 'content': dict}
Format 2: {'commands': list[str], 'callback': bool} - for common batch commands""" + f"""\nUser Prompt: "{prompt}"
Current Directory Content: {dir_content}
For extra info, the current directory path: {getcwd()}"""
        response = self._send(batchPrompt)

        try: clean = json.loads(response.text)
        except: clean = self._clean(response.text)
        run_history = "```batch\n"

        if 'type' in clean:
            if clean['type'] == 'writeInFile':
                if 'fileContent' not in clean['content'] or 'path' not in clean['content']:
                    print(clean)
                    raise Exception("Missing content or path in writeInFile command.")
                path = clean['content']['path']
                content = clean['content']['fileContent']
                self._editFile(content, path)

        if 'callback' in clean:
            cb = 0
            while clean.get('callback', False):
                print("Response before handling callbacks:", clean)
                if cb > 5: 
                    run_history += "Callback limit reached (5/5). Exiting..."
                    break
                cb += 1
                leg, cbstr = self._handleCommands(clean, True)
                run_history += ("Callback history: \n" + leg + '\n\n-----------------------------------\n\n')
                if cbstr: 
                    response = self._send(f"SYSTEM RETURN: Callback from your last request (feel free to callback again if you still need more info or some error occurred): {cbstr}\nIncase of updates on the current directory: {getcwd()}\n")
                
                try: 
                    clean = json.loads(response.text)
                except: 
                    clean = self._clean(response.text)

                if 'callback' not in clean or not clean.get('callback', False):
                    break

        run_history += self._handleCommands(clean)
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
        if run_history:
            print("\nRun history:")
            print(Markdown(run_history))
        print("\n[bold white]Command executed successfully.")