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

        if '```' not in response.text:
            return f"```python" + response.text + "```"
        return response.text

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
        
        exec(code.replace("```python", "").replace("```", ""))

if __name__== "__main__":
    pygen = PyGenerator()
    response = pygen.ask("create a simple API that return the sum of the parameters (ints)")

    md = Markdown(response)
    print("Results: ")
    print(md)

    ask = input("Do you want to run the script? (Y/N)")
    if ask not in ['sim', 's', 'y', 'yes']: 
        exit()

    pygen.run(response)