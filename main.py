import ollama
import os
import subprocess

model="llama3"
context="""I am an automated program (in the form of a python script). 
    A user is talking to me, and through me to you: I will forward the user input to you and ask you to help me understand it.
    You are an AI designed to understand the user's requests and help me run the adequate checks and processes. Your name is AIfred.
    I can understand only a limited subset of requests by the user so I will need your LLM capabilities to understand the user's intent."""

def get_file_info(path='.'):
    file_info = []
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            size = os.path.getsize(full_path)
            file_info.append((full_path, size))
    return file_info

def find_file(name, path='.'):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return None

def run_command(command):
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout

def process_query(query):
    category_prompt = f"""{context}
    Have a look at the user input and simply answer any of these categories' names, without any other comment, if it applies:
      - Category Name: 'LIST_FILES', for when the user asks for a list of files,
      - Category Name: 'FIND_FILE', for when the user is trying to find a file or a folder,
      - Category Name: 'FILE_INFO', for when the user is trying to get other information about files or folders,
      - Category Name: 'OTHER', for the rest of the cases, when the user is asking something else.
   
    Your answer must not contain anything else than one of the category names I gave you.
    You must not include anything else in your answer than the capitalized category name. No label, no introduction, nothing.
    For instance you must not answer with 'The category is LIST_FILES', you must not answer with CATEGORY NAME: LIST_FILES, you must simply answer with:
      LIST_FILES
    
    The user input is: {query}"""
    category_response = ollama.generate(model=model, prompt=category_prompt)
    category = category_response['response'].strip()
    print("llama2 response for categorization:", category);

    if category == "LIST_FILES":
        files = os.listdir('.')
        return f"Files in current directory: {files}"
    
    elif category == "FIND_FILE":
        file_prompt = f"Extract the file or directory name to search for from the user input. This program does not understand natural language so please simply answer the path name and nothing else, do not introduce your answer either. For instance if the user input is 'Where is document.txt in my computer?' you would simply answer with 'document.txt' without the quotes. User query: {query}"
        file_response = ollama.generate(model=model, prompt=file_prompt)
        file_name = file_response['response'].strip()
        result = find_file(file_name)
        return f"File '{file_name}' found at: {result}" if result else f"File '{file_name}' not found."
    
    elif category == "FILE_INFO":
        files = get_file_info()
        if "biggest" in query.lower():
            biggest = max(files, key=lambda x: x[1])
            return f"The biggest file is '{biggest[0]}' with size {biggest[1]} bytes."
        else:
            return f"File information: {files}"
    
    elif category == "RUN_COMMAND":
        command_prompt = f"Extract the command to run from this query: {query}"
        command_response = ollama.generate(model=model, prompt=command_prompt)
        command = command_response['response'].strip()
        output = run_command(command)
        return f"Command output: {output}"
    
    else:  # OTHER
        general_response = ollama.generate(model=model, prompt=f"{context} For this one, the user is talking directly to you, so answer him directly. The user input is: {query}")
        return general_response['response']

def main():
    while True:
        query = input("Enter your question (or 'quit' to exit): ")
        
        if query.lower() == 'quit':
            break

        response = process_query(query)
        print("Response:", response)

if __name__ == "__main__":
    main()