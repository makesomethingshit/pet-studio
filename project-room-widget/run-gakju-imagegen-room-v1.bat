@echo off
start "Pet Studio Widget" /min pythonw "%~dp0pet_studio_widget.py" --kit "%~dp0..\runs\gakju-imagegen-room-v1\kit" --scale 1.25 --x 1200 --y 620
