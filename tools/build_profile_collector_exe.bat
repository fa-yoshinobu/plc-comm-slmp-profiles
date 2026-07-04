@echo off
setlocal

set "ROOT=%~dp0.."
pushd "%ROOT%" || exit /b 1

python -m PyInstaller --onefile ^
  --name slmp-profile-collector ^
  --add-data "capability\slmp_builtin_ethernet_profiles.json;capability" ^
  --add-data "device-ranges\slmp_device_range_rules.json;device-ranges" ^
  tools\collect_live_plc_profile.py
if errorlevel 1 (
  popd
  exit /b 1
)

if exist build rmdir /s /q build
if exist slmp-profile-collector.spec del /q slmp-profile-collector.spec
if exist tools\__pycache__ rmdir /s /q tools\__pycache__

echo Built dist\slmp-profile-collector.exe
popd
