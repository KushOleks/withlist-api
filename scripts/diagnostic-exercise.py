"""One participant selects a fault; the diagnostician sees only symptoms.

Run from the API repository. Uses only disposable lab05-diagnostic resources.
"""
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.chdir(root)
print('Choose a fault without telling the diagnostician:')
print('1. Bind API to loopback inside its container')
print('2. Forward the host API port to the wrong container port')
print('3. Use a nonexistent PostgreSQL hostname')
choice = input('Enter 1, 2 or 3: ').strip()
patches = {
    '1': 'services:\n  api:\n    command: ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]\n',
    '2': 'services:\n  api:\n    ports: !override\n      - "127.0.0.1:19000:8001"\n',
    '3': 'services:\n  api:\n    environment:\n      DB_HOST: postgres-missing\n',
}
if choice not in patches:
    raise SystemExit('Invalid choice; no changes made')
patch = root / '.lab05-diagnostic.yaml'
patch.write_text(patches[choice])
env = dict(os.environ, API_PORT='19000', UI_PORT='19080')
env_file = '.env.lab05' if Path('.env.lab05').exists() else '.env'
base = ['docker', 'compose', '-p', 'lab05-diagnostic', '--env-file', env_file, '-f', 'compose.yaml']
subprocess.run(base + ['up', '-d', '--wait', '--wait-timeout', '120'], check=True, env=env)
subprocess.run(base + ['-f', str(patch), 'up', '-d', '--no-deps', 'api'], check=True, env=env)
print('Fault applied only to lab05-diagnostic. Tell the diagnostician: ready; API URL http://localhost:19000')
