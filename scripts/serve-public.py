"""Loopback preview of scanned public files only, with MP4 range support."""
from pathlib import Path
import argparse,functools,importlib.util
from http.server import ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=3036);a=p.parse_args();report=load('public_scan','secret-scan.py').scan()
 if not report['ok']:raise ValueError('Resolve public-file scan failures before preview')
 allowed=frozenset(row['path'] for row in report['entries']);handler=functools.partial(load('public_demo','serve-demo.py').DemoHandler,directory=str(ROOT),allowed=allowed)
 server=ThreadingHTTPServer(('127.0.0.1',a.port),handler);print(f'http://127.0.0.1:{a.port}/',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
