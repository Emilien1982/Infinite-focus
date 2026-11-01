import os
import shutil
import stat
import subprocess

BASE_DIR = "/Users/utilisateur/dev_ai/Infinite Focus"
APP_DIR = os.path.join(BASE_DIR, "Infinite Focus.app")
CONTENTS_DIR = os.path.join(APP_DIR, "Contents")
MACOS_DIR = os.path.join(CONTENTS_DIR, "MacOS")
RESOURCES_DIR = os.path.join(CONTENTS_DIR, "Resources")

# Clean previous build if any
if os.path.exists(APP_DIR):
    shutil.rmtree(APP_DIR)

os.makedirs(MACOS_DIR, exist_ok=True)
os.makedirs(RESOURCES_DIR, exist_ok=True)

# Copy AppIcon.icns
icon_src = os.path.join(BASE_DIR, "AppIcon.icns")
if os.path.exists(icon_src):
    shutil.copy2(icon_src, os.path.join(RESOURCES_DIR, "AppIcon.icns"))

# Create PkgInfo
with open(os.path.join(CONTENTS_DIR, "PkgInfo"), "w") as f:
    f.write("APPL????")

# Create Info.plist
info_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>fr_FR</string>
    <key>CFBundleExecutable</key>
    <string>Infinite Focus</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.antigravity.infinitefocus</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Infinite Focus</string>
    <key>CFBundleDisplayName</key>
    <string>Infinite Focus</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>NSMicrophoneUsageDescription</key>
    <string>Infinite Focus diffuse de la musique générative locale.</string>
</dict>
</plist>
"""
with open(os.path.join(CONTENTS_DIR, "Info.plist"), "w") as f:
    f.write(info_plist)

# Create Launcher Script
launcher_script = f"""#!/bin/bash
PROJECT_DIR="{BASE_DIR}"
cd "$PROJECT_DIR" || exit 1

export PATH="/Users/utilisateur/.local/bin:/opt/homebrew/bin:$PATH"
export PYTHONUNBUFFERED=1

exec "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/main.py" "$@"
"""

launcher_path = os.path.join(MACOS_DIR, "Infinite Focus")
with open(launcher_path, "w") as f:
    f.write(launcher_script)

# Make launcher executable
st = os.stat(launcher_path)
os.chmod(launcher_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

print(f"Built bundle at {APP_DIR}")

# Install to /Applications and ~/Applications
targets = ["/Applications/Infinite Focus.app", "/Users/utilisateur/Applications/Infinite Focus.app"]
for target in targets:
    try:
        if os.path.islink(target) or os.path.exists(target):
            if os.path.islink(target) or os.path.isfile(target):
                os.unlink(target)
            else:
                shutil.rmtree(target)
        os.symlink(APP_DIR, target)
        print(f"Installed symlink at {target}")
    except Exception as e:
        print(f"Could not install to {target}: {e}")

print("Installation completed successfully!")
