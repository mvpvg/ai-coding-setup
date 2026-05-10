@echo off
rem exec() used for try/except in single-line python -c context on Windows CMD; data is from stdin, not user input
python -c "import json,sys,os;from datetime import datetime,timezone;from pathlib import Path;data={};exec('try:\n data.update(json.load(sys.stdin))\nexcept: pass');lp=Path(os.environ.get('USERPROFILE',str(Path.home())))/'.claude'/'audit.log';lp.parent.mkdir(parents=True,exist_ok=True);entry={'ts':datetime.now(timezone.utc).isoformat(),'event':'tool_result','tool':data.get('tool_name',''),'exit_code':int(data.get('exit_code',0))};open(str(lp),'a',encoding='utf-8').write(json.dumps(entry,separators=(',',':'))+chr(10))" 2>nul
exit /b 0
