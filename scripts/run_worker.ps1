$env:STONKS_TEST = 'true'
$env:ALPACA_MODE = 'paper'
$env:TICK_SECONDS = '300'
Set-Location 'D:\ai_ag_hack_alpaca'
python -m uvicorn stonks.api:app --host 127.0.0.1 --port 8000
