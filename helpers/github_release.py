import requests

def get_latest_release(owner, repo):
    url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
owner = 'bitesizing'
repo = 'mot-task'
latest_release = get_latest_release(owner, repo)