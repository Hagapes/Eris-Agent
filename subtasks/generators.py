import requests

class Python:
    def __init__(self):
        self.TARGET = "https://www.codeconvert.ai/api/free-generate"
        self.headers = {
            'origin': 'https://www.codeconvert.ai',
            'referer': 'https://www.codeconvert.ai/python-code-generator',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        }
        
    def ask(self, prompt):
        payload = {
            "inputText": prompt,
            "inputLang": "Python"
        }

        response = requests.post(self.TARGET, headers=self.headers, data=payload)

        if response.status_code not in [200, 201]:
            raise Exception(f"Request error: Anormal status code: {response.status_code}")
        
        try: return response.json()
        except: return response.text

if __name__ == "__main__":
    py = Python()
    print("Generating code...")
    print(py.ask("create a simple CLI that converts specific types of files into other e.g: CSV to JSON")['outputCodeText'])