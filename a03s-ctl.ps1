$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$scriptDir\a03s-ctl.py" @args
