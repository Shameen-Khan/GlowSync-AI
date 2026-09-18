import os,subprocess,sys,time,tempfile,socket
from pathlib import Path
from urllib.request import urlopen
root=Path(__file__).resolve().parents[1];children=[]
with tempfile.TemporaryDirectory() as tmp:
 def port():
  with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
 web,java=port(),port()
 env=os.environ.copy();env.update(GLOWSYNC_DATABASE=str(Path(tmp)/'test.db'),GLOWSYNC_PORT=str(web),GLOWSYNC_JAVA_PORT=str(java),GLOWSYNC_ROOT=str(root),GLOWSYNC_TEST_BASE=f'http://127.0.0.1:{web}')
 try:
  children.append(subprocess.Popen(['java','-cp',str(root/'java'),'ShadeService'],env=env,stdout=subprocess.DEVNULL))
  children.append(subprocess.Popen([sys.executable,'-m','backend.serve'],cwd=root,env=env,stdout=subprocess.DEVNULL))
  for _ in range(80):
   try:
    with urlopen(f'http://127.0.0.1:{web}/api/health',timeout=.5) as r:
     if r.status==200:break
   except OSError:time.sleep(.1)
  result=subprocess.run(['node',str(root/'tests/ui.cjs')],env=env)
  sys.exit(result.returncode)
 finally:
  for child in children:child.terminate()
  for child in children:
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:child.kill()
