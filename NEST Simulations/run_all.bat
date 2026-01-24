@echo off
for /F "tokens=1,2 delims=," %%A in (tokens.txt) do (
    start "%%B" cmd /k python nest_sim.py %%A %%B
)