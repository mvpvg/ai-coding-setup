@echo off
python -c "import json,sys,os;from datetime import datetime,timezone;from pathlib import Path;data=json.load(sys.stdin) if True else {};lp=Path(os.environ.get('USERPROFILE',str(Path.home())))/'.claude'/'audit.log';lp.parent.mkdir(parents=True,exist_ok=True);entry={'ts':datetime.now(timezone.utc).isoformat(),'event':'tool_result','tool':data.get('tool_name',''),'exit_code':int(data.get('exit_code',0))};open(str(lp),'a').write(json.dumps(entry,separators=(',',':'))+chr(10))" 2>nul
exit /b 0
