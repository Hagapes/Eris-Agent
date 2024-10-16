import requests
import subprocess
import sys
import importlib.util
import io
from contextlib import redirect_stdout
from rich import print
from rich.console import Console
from rich.markdown import Markdown
from os import makedirs, environ
from os.path import exists

class PythonCodeGenerator:
    def __init__(self):
        self.TARGET = "https://smartcodewriter.com/wp-admin/admin-ajax.php"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept": "/",
            "Accept-Encoding": "identifier",
        }
        self.console = Console()

    def install_module(self, lib):
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", lib], check=True)
        except subprocess.CalledProcessError as e:
            raise ImportError(f"Couldn't install the required library {lib}. Error: {str(e)}")

    def run(self, code):
        for line in code.split('\n'):
            if line.startswith("import") or line.startswith("from"):
                parsedLine = line.split()
                lib = parsedLine[1]

                if importlib.util.find_spec(lib) is None:
                    print(f"[bold yellow][INFORMATION][/] Module {lib} not found, attempting to install.")
                    self.install_module(lib)

        try:
            exec(code.replace("```python", "").replace("```", ""))
            return f"The code was executed successfully.\nGenerated code: \n{code}"
        except Exception as e:
            return f"An error occurred while executing the code: {e}\nFor context, the code: {code}"

    def ask(self, prompt: str):
        payload = {
            "action": "generate_python_code",
            "question": prompt,
            "special_instruction": ""
        }

        response = requests.post(self.TARGET, headers=self.headers, data=payload)

        if response.status_code != 200:
            raise Exception(f"Request error: Anormal status code: {response.status_code}")

        if '```' not in response.text:
            return f"```python\n{response.text}\n```"
        return response.text

    def inject(self, prompt: str, action: str = "execute"):
        code = self.ask(prompt)

        if action == "execute":
            print(Markdown(code))
            print("[bold red][IMPORTANT][/] The AI suggested executing the code above to complete the task.")
            rp = self.console.input("[bold white]Do you want to execute the code? (Y/N) ")
            if rp.lower() not in ['y', 'yes']:
                print("[bold red]Aborting task...[/]")
                return False
            captured_output = self.run(code)
            return captured_output
        elif action == "store":
            makedirs("subtasks/output", exist_ok=True)
            pend = 0
            name = "output"
            while exists(f"subtasks/output/{name}.py"):
                pend += 1
                name = "output" + str(pend)
            with open(f"subtasks/output/{name}.py", "w") as f:
                f.write(code.replace("```python", "").replace("```", ""))
            print(f"[bold green]Code stored at subtasks/output/{name}.py![/]")
            return f"CODE_STORE OUTPUT: Code generated and stored at subtasks/output/{name}.py successfully!"

if __name__ == "__main__":
    py_gen = PythonCodeGenerator()
    print("Generating code...")
    output = py_gen.inject("create a random code", 'store')
