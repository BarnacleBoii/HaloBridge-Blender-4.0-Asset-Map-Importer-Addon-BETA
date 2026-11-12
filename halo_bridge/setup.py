"""Installation discovery and diagnostics; never installs third-party software."""
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path


def steam_libraries():
    roots=[]
    if os.name=='nt':
        import winreg
        for hive,key,value in ((winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam','SteamPath'),
                               (winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\WOW6432Node\Valve\Steam','InstallPath')):
            try:
                with winreg.OpenKey(hive,key) as handle:roots.append(Path(winreg.QueryValueEx(handle,value)[0]))
            except OSError:pass
    roots.append(Path(os.environ.get('PROGRAMFILES(X86)','C:/Program Files (x86)'))/'Steam')
    libraries=list(roots)
    for root in roots:
        file=root/'steamapps/libraryfolders.vdf'
        if not file.is_file():continue
        try:
            for path in re.findall(r'"path"\s*"([^"\r\n]+)"',file.read_text(encoding='utf-8',errors='replace')):
                libraries.append(Path(path.replace('\\\\','\\')))
        except OSError:pass
    return list(dict.fromkeys(libraries))


def runtime_check():
    candidates=[shutil.which('dotnet'),str(Path(os.environ.get('PROGRAMFILES','C:/Program Files'))/'dotnet/dotnet.exe')]
    for exe in candidates:
        if not exe or not Path(exe).is_file():continue
        try:
            run=subprocess.run([exe,'--list-runtimes'],capture_output=True,text=True,timeout=10,
                               creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if run.returncode==0 and re.search(r'^Microsoft.WindowsDesktop.App 10\.',run.stdout,re.M):return True
        except (OSError,subprocess.SubprocessError):pass
    return False


def check(config,addon_dir):
    issues=[]
    if os.name!='nt' or platform.machine().lower() not in ('amd64','x86_64'):
        issues.append('This alpha requires 64-bit Windows.')
    from . import games
    kit=Path(config['kit']);game=games.GAMES.get(config.get('game','halo3'),games.GAMES['halo3'])
    # Import-only games (Halo CE, Halo 2) read MCC .map files; their kits have no ManagedBlam
    # and are optional. Prepare still checks the Halo 3 / ODST destination kit separately.
    import_only=game.get('classic') or not (game.get('sapien_enabled') or game.get('scenario_enabled'))
    if not import_only:
        for item in ('tool.exe','sapien.exe','bin/ManagedBlam.dll'):
            if not (kit/item).is_file():issues.append('Select the '+game['label']+' Editing Kit folder ('+game.get('kit','')+'); missing '+item+'.')
    elif game.get('classic') and config.get('kit') and not (kit/'tool.exe').is_file():
        issues.append('Optional: select the '+game['label']+' Editing Kit folder ('+game.get('kit','')+') to import its .scenario tags; tool.exe was not found.')
    sky=game.get('sky','')
    if sky and not (kit/'tags'/(sky.replace('\\','/')+'.scenario')).is_file():
        issues.append('Extract the Editing Kit tag archives; '+sky+'.scenario is required for starter sky settings.')
    maps=Path(config['maps'])
    if not maps.is_dir() or not any(maps.glob('*.map')):
        issues.append('Select the installed MCC maps folder for the chosen game containing .map files.')
    for name in ('extractor/HaloBridge.Extractor.exe','tags/HaloBridge.Tags.exe'):
        if not (Path(addon_dir)/'bin'/name).is_file():
            issues.append('Helper missing: '+name+'. Install the release add-on ZIP, or build helpers from source.')
    if not runtime_check():issues.append('Install Microsoft .NET 10 Desktop Runtime for Windows x64, then restart Blender.')
    if os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full',0,winreg.KEY_READ|winreg.KEY_WOW64_32KEY) as key:
                if winreg.QueryValueEx(key,'Release')[0]<528040:raise OSError()
        except OSError:issues.append('Install .NET Framework 4.8 or newer for the scenario helper.')
    return issues
