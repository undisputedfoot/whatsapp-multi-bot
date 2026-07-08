"""Install Node.js and npm dependencies for the WhatsApp engine."""
import subprocess, os, sys, urllib.request, zipfile, shutil

engine_dir = os.path.join(os.path.dirname(__file__), 'wa-engine')
node_dir = os.path.expanduser('~/nodejs')
node_exe = os.path.join(node_dir, 'node.exe')
npm_cmd = os.path.join(node_dir, 'npm.cmd')

# Install Node.js if not found
if not os.path.exists(node_exe):
    print('Downloading Node.js v22...')
    url = 'https://nodejs.org/dist/v22.14.0/node-v22.14.0-win-x64.zip'
    zip_path = os.path.expanduser('~/node.zip')
    urllib.request.urlretrieve(url, zip_path)
    print('Extracting...')
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(os.path.expanduser('~'))
    os.rename(os.path.expanduser('~/node-v22.14.0-win-x64'), node_dir)
    os.remove(zip_path)
    print('Node.js installed!')
else:
    print('Node.js already installed')

v = subprocess.run([node_exe, '--version'], capture_output=True, text=True)
print(f'Node {v.stdout.strip()}')

# Install npm deps
print('Installing wa-engine dependencies...')
sys.stdout.flush()
result = subprocess.run(
    [npm_cmd, 'install'],
    cwd=engine_dir,
    capture_output=True,
    text=True,
    timeout=180,
)
print(result.stdout[-500:])
if result.returncode == 0:
    print('SUCCESS: npm install completed!')
else:
    print(f'FAILED (code {result.returncode}):')
    print(result.stderr[-500:])
