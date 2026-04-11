import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

# Connect to GitHub using our token
g = Github(os.getenv("GITHUB_TOKEN"))


def get_repo_structure(repo_name):
    #lets the agent see what files exist in any github repo
    try:
        repo = g.get_repo(repo_name)
        contents = repo.get_contents("")
        files = []
        
        #this loop goes through all files and content
        while contents:
            file = contents.pop(0)
            if file.type == "dir":
                #if its a folder look inside it too
                contents.extend(repo.get_contents(file.path))
            else:
                #if its a file add it to our list
                files.append(file.path)       
        
        return "\n".join(files)
    
    except Exception as e:
        return f"Error getting repo structure: {e}"
    
    
#in this section the agents read any file inside a github repo
def get_file_content(repo_name, file_path):
        
    try:
        repo = g.get_repo(repo_name)
        file = repo.get_contents(file_path)
        # file.decoded_content gives us the raw bytes
         # .decode("utf-8") converts bytes to readable text
        return file.decoded_content.decode("utf-8")
        
    except Exception as e:
        return f"Error getting file content: {e}"
    
    

def create_pull_request(repo_name, title, body, filename, content, branch_name):
    try:
        repo = g.get_repo(repo_name)

        # get the main branch
        main_branch = repo.get_branch("main")

        # create a new branch from main
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=main_branch.commit.sha
        )

        # get the current file
        file = repo.get_contents(filename)

        # update the file on new branch
        repo.update_file(
            path=filename,
            message=f"DevAgent: {title}",
            content=content,
            sha=file.sha,
            branch=branch_name
        )

        # open the pull request
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base="main"
        )

        return f"Pull Request created! URL: {pr.html_url}"

    except Exception as e:
        return f"Error creating PR: {e}"