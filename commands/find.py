from subprocess import run as system

def find(filename):
    response = system(f'es {filename}', shell=True, capture_output=True, text=True)
    if response.stderr: raise Exception(response.stderr)
    if not response.stdout: return None

    return response.stdout.strip().split('\n')

if __name__ == '__main__':
    print(find('main.py'))