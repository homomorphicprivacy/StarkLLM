@echo off
rem start.cmd — identical to start.bat.
rem Windows Explorer sometimes blocks .bat files downloaded from the internet
rem but leaves .cmd files alone. If start.bat is blocked, try this file instead.
call "%~dp0start.bat"
