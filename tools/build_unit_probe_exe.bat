@echo off
rem Build standalone single-file executables for the unit probe tools.
rem Run from the repository root: tools\build_unit_probe_exe.bat
cd /d "%~dp0.."

python -m PyInstaller --onefile --clean ^
  --name slmp-unit-probe-plan ^
  --add-data "capability\slmp_ethernet_profiles.json;capability" ^
  --add-data "tools\unit_probe_plan_required.json;tools" ^
  tools\run_unit_probe_plan.py
if errorlevel 1 exit /b 1

python -m PyInstaller --onefile --clean ^
  --name slmp-live-probe ^
  --add-data "capability\slmp_ethernet_profiles.json;capability" ^
  tools\live_profile_probe.py
if errorlevel 1 exit /b 1

if exist build rmdir /s /q build
if exist slmp-unit-probe-plan.spec del /q slmp-unit-probe-plan.spec
if exist slmp-live-probe.spec del /q slmp-live-probe.spec

echo Built dist\slmp-unit-probe-plan.exe and dist\slmp-live-probe.exe
echo Hand off the exe together with a reviewed plan JSON and tools\UNIT_PROBE_PLAN_USAGE.md.
