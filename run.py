"""Start GlowSync locally. No Node, npm, external account or cloud database required."""
import hashlib
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parent

def main():
 os.chdir(ROOT)
 java_port=int(os.environ.setdefault('GLOWSYNC_JAVA_PORT','8081'))
 web_port=int(os.environ.setdefault('GLOWSYNC_PORT','8000'))
 if java_port==web_port or any(not 1024<=p<=65535 for p in (java_port,web_port)):
  raise RuntimeError('Choose two different ports between 1024 and 65535.')
 for port in (java_port,web_port):
  with socket.socket() as probe:
   try: probe.bind(('127.0.0.1',port))
   except OSError: raise RuntimeError(f'Port {port} is busy. Stop the old app or set GLOWSYNC_PORT / GLOWSYNC_JAVA_PORT.') from None
 java=shutil.which('java');javac=shutil.which('javac')
 if not java: raise RuntimeError('Java is missing. Install JDK 17 or newer and restart VS Code.')
 if javac:
  subprocess.run([javac,'--release','17','java/ShadeService.java'],check=True)
 else:
  expected=(ROOT/'java/source.sha256').read_text(encoding='utf-8').strip()
  if expected!=hashlib.sha256((ROOT/'java/ShadeService.java').read_bytes()).hexdigest() or not (ROOT/'java/ShadeService.class').exists():
   raise RuntimeError('Install a full JDK 17+ to compile the changed Java source.')
 from backend.app import create_app
 create_app() # Validates dependencies and initializes the local catalogue before spawning.
 children=[]
 try:
  for command,url in [([java,'-cp','java','ShadeService'],f'http://127.0.0.1:{java_port}/health'),([sys.executable,'-m','backend.serve'],f'http://127.0.0.1:{web_port}/api/health')]:
   child=subprocess.Popen(command);children.append(child)
   for _ in range(120):
    if child.poll() is not None: raise RuntimeError('A service failed to start. Read the error above.')
    try:
     with urlopen(url,timeout=1) as response:
      if response.status==200: break
    except OSError: time.sleep(.1)
   else: raise RuntimeError('A service did not become ready.')
  print(f'\nGlowSync is ready: http://127.0.0.1:{web_port}\nKeep this terminal open. Press Ctrl+C to stop.\n',flush=True)
  while all(c.poll() is None for c in children): time.sleep(.5)
  raise RuntimeError('A backend stopped unexpectedly.')
 except KeyboardInterrupt: print('\nStopping GlowSync.')
 finally:
  for child in reversed(children):
   if child.poll() is None:
    child.terminate()
    try: child.wait(timeout=5)
    except subprocess.TimeoutExpired: child.kill();child.wait()

if __name__=='__main__':
 try: main()
 except (RuntimeError,ImportError,ValueError,subprocess.CalledProcessError) as e:
  print(f'\nSetup error: {e}\nSee README.md for installation steps.',file=sys.stderr);sys.exit(1)
