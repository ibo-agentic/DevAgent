import os

def read_file(filepath):
    #try to open the file and read it
    #if file doesn't exist, return an error message
    
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"
    
def list_files(folder_path):
    try:
        files = os.listdir(folder_path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {e}"
        