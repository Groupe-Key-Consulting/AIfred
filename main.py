import ollama
import os
import subprocess
import chainlit as cl
import requests
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_random_joke():
    """
    Fetches a random joke from an API.

    Returns:
    str: A string containing a joke, or an error message
    """
    logging.info("Fetching a random joke")
    joke_url = "https://official-joke-api.appspot.com/random_joke"

    try:
        response = requests.get(joke_url)
        response.raise_for_status()
        joke_data = response.json()
        joke = f"{joke_data['setup']} - {joke_data['punchline']}"
        logging.info(f"Random joke: {joke}")
        return joke
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred while fetching joke: {str(e)}")
        return f"An error occurred while fetching a joke: {str(e)}"

def find_file(name, path='.'):
    logging.info(f"Looking for file {name} in path {path}")
    try:
        for root, dirs, files in os.walk(path):
            if name in files:
                logging.info(f"Found file {name} at path {os.path.join(root, name)}")
                return f"File found at path {os.path.join(root, name)}"
        return f"File '{name}' not found in path '{path}'."
    except Exception as e:
        return f"An error occurred: {str(e)}"

modelName="llama3.1"
# I am an automated program (in the form of a python script). 
# A user is talking to me, and through me to you: I will forward the user input to you and ask you to help me understand it.
# I can understand only a limited subset of requests by the user so I will need your LLM capabilities to understand the user's intent.

context="""You are an AI designed to understand the user's requests and help me run the adequate checks and processes.
Your name is AIfred. Use the tools provided."""


# Define tools (functions) that can be called by the AI model
tools = [
    {
        "name": "find_file",
        "description": "Find the path of a file from its name",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The file name to search for",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_random_joke",
        "description": "Get a random joke",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    }
]

# Initialize the AI model
model = OllamaFunctions(model=modelName,
                        format="json", temperature=0)
model = model.bind_tools(tools=tools)

# Create the prompt template for the AI model
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=context),
    ("human", "{input}"),
])

def get_file_info(path='.'):
    file_info = []
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            size = os.path.getsize(full_path)
            file_info.append((full_path, size))
    return file_info


def run_command(command):
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout

# def process_query(query):
#     category_prompt = f"""{context}
#     Have a look at the user input and simply answer any of these categories' names, without any other comment, if it applies:
#       - Category Name: 'LIST_FILES', for when the user asks for a list of files,
#       - Category Name: 'FIND_FILE', for when the user is trying to find a file or a folder,
#       - Category Name: 'FILE_INFO', for when the user is trying to get other information about files or folders,
#       - Category Name: 'FILE_NAME', for when the user is asking about file names,
#       - Category Name: 'OTHER', for the rest of the cases, when the user is asking something else.
   
#     Your answer must not contain anything else than one of the category names I gave you.
#     You must not include anything else in your answer than the capitalized category name. No label, no introduction, nothing.
#     For instance you must not answer with 'The category is LIST_FILES', you must not answer with CATEGORY NAME: LIST_FILES, you must simply answer with:
#       LIST_FILES
    
#     The user input is: {query}"""
#     category_response = ollama.generate(model=model, prompt=category_prompt)
#     category = category_response['response'].strip()
#     print(f"{model} response for categorization: {category}");

#     if category == "LIST_FILES":
#         files = os.listdir('.')
#         return f"Files in current directory: {files}"
    
#     elif category == "FILE_NAME":
#         files = get_file_info()
#         # map file info to a string with file names and sizes
#         files_str = ', '.join([f"{file[0]} ({file[1]} bytes)" for file in files])
#         prompt = f"""Given these files, answer the user's query:
#           {files_str}

#           User query: {query}"""
#         print("Prompt for file name extraction:", prompt)
#         response = ollama.generate(model=model, prompt=prompt)
#         return response['response']

#     elif category == "FIND_FILE":
#         file_prompt = f"Extract the file or directory name to search for from the user input. This program does not understand natural language so please simply answer the path name and nothing else, do not introduce your answer either. For instance if the user input is 'Where is document.txt in my computer?' you would simply answer with 'document.txt' without the quotes. User query: {query}"
#         file_response = ollama.generate(model=model, prompt=file_prompt)
#         file_name = file_response['response'].strip()
#         result = find_file(file_name)
#         return f"File '{file_name}' found at: {result}" if result else f"File '{file_name}' not found."
    
#     elif category == "FILE_INFO":
#         files = get_file_info()
#         if "biggest" in query.lower():
#             biggest = max(files, key=lambda x: x[1])
#             return f"The biggest file is '{biggest[0]}' with size {biggest[1]} bytes."
#         else:
#             return f"File information: {files}"
    
#     elif category == "RUN_COMMAND":
#         command_prompt = f"Extract the command to run from this query: {query}"
#         command_response = ollama.generate(model=model, prompt=command_prompt)
#         command = command_response['response'].strip()
#         output = run_command(command)
#         return f"Command output: {output}"
    
#     else:  # OTHER
#         general_response = ollama.generate(model=model, prompt=f"{context} For this one, the user is talking directly to you, so answer him directly. The user input is: {query}")
#         return general_response['response']

def process_query(query):
    """
    Processes user queries by invoking the AI model and calling appropriate functions.

    Args:
    query (str): The user's input query

    Returns:
    str: The response to the user's query
    """
    logging.info(f"Processing query: {query}")
    formatted_prompt = prompt.format_messages(input=query)
    logging.debug(f"Formatted prompt: {formatted_prompt}")
    result = model.invoke(formatted_prompt)
    logging.info(f"Model result: {result}")

    if result.tool_calls:
        for tool_call in result.tool_calls:
            function_name = tool_call['name']
            args = tool_call['args']
            logging.info(f"Function call: {function_name}, Args: {args}")

            if function_name == "find_file":
                return find_file(**args)
            elif function_name == "get_random_joke":
                return get_random_joke()

    return result.content

# Chainlit event handler for chat start
@cl.on_chat_start
async def start():
    """
    Initializes the chat session.
    """
    logging.info("Chat started")
    cl.user_session.set("model", model)

# Chainlit event handler for incoming messages


@cl.on_message
async def main(message: cl.Message):
    """
    Handles incoming user messages, processes them, and sends responses.

    Args:
    message (cl.Message): The incoming user message
    """
    logging.info(f"Received message: {message.content}")
    try:
        response = await cl.make_async(process_query)(message.content)
        logging.info(f"Response: {response}")
        await cl.Message(content=response).send()
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logging.error(f"Error: {error_message}")
        await cl.Message(content=error_message).send()

# def main():
#     while True:
#         query = input("Enter your question (or 'quit' to exit): ")
        
#         if query.lower() == 'quit':
#             break

#         response = process_query(query)
#         print("Response:", response)

# if __name__ == "__main__":
#     main()