# 🤖 ErisAgent

ErisAgent is an advanced automation system that uses Google's Gemini model to handle a wide range of tasks, from file management and code execution to online searches. It is designed to dynamically respond to user prompts and execute different types of commands such as writing files, running terminal commands, generating code, and searching the web.

## ✨ Features

- **🧑‍💻 Code Generation**: Automatically generates Python code based on user inputs.
- **🌐 Web Search**: Uses Tavily API for web searches.
- **📂 File Management**: Finds, reads, writes, and manages files on your system.
- **💻 Terminal Commands**: Executes terminal commands directly from Python.
- **🤝 Interaction**: Prompts the user for inputs when necessary, with flexible response options.

## 🛠️ Prerequisites

Before running the project, you need to have the following environment variables set:

- 🔑 `GOOGLE_API_KEY`: API key for Google's Gemini model.
- 🔍 `SEARCH-TOKEN`: API key for the Tavily search API.

You will also need to install the [Everything Command-line Interface](https://www.voidtools.com/downloads/#cli) for `find.py` to work.

## 📁 Project Structure

```
.
├── main.py            # Main agent logic.
├── commands/
│   ├── find.py        # Module to find files.
│   ├── generators.py  # Wrap for the code generation tool (this might not be available in future versions)
│   ├── search.py      # Web search logic using Tavily API.
└── systemrules.txt    # Base system instructions for the AI.
```

### `main.py`

This file contains the main logic for the ErisAgent, handling AI interactions, processing different types of requests (code execution, file operations, web searches), and generating responses.

- **🧠 `think()`**: Main function that processes user prompts and communicates with the AI.
- **⚙️ `_process()`**: Handles specific types of AI requests, such as code execution, file reading, and web searches.
- **🔄 `_returnToAI()`**: Sends the results of tasks back to the AI for further instructions.

### `commands/find.py`

A helper function that searches for a file in the system using the `es` command. It returns the paths of matching files.

### `commands/generators.py`

Handles code generation using an external API. It can execute the generated code or store it in a file.

### `commands/search.py`

Integrates with the Tavily API to perform online searches based on the user's queries.

## 🚀 How to Run

1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2. Set up environment variables:
    ```bash
    export GOOGLE_API_KEY="your-google-api-key"
    export SEARCH-TOKEN="your-search-api-key"
    ```

3. Install the requirements:
    ```bash
    pip install -r requirements.txt
    ```

4. Run the main agent:
    ```bash
    python main.py
    ```

5. The agent will prompt you for commands. You can type your requests, and the system will process them.

## 📝 Example Usage

```
current/directory >> find myfile.txt
INFORMATION 🔎 Searching for file 'myfile.txt'...
[A.I] File 'myfile.txt' found at path/to/myfile.txt

current/directory >> write_file
INFORMATION 📝 Writing to file 'output.txt'...

current/directory >> search Python tutorials
INFORMATION 🚢 Navigating on the web...
[A.I] *python tutorials info
```

This will print additional information during execution.

## 📄 License

This project is licensed under the MIT License.
