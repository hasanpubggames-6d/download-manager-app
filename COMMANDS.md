# Quick Reference: Termux Commands for Building APK

## Full Termux Setup Commands (Copy-Paste Ready)

```bash
# 1. Update Termux
pkg update && pkg upgrade -y

# 2. Install required packages
pkg install -y python python-pip build-essential libffi openssl libxml2 libxslt jpeg png sqlite git openjdk-17 android-tools

# 3. Grant storage permission (answer yes)
termux-setup-storage

# 4. Set environment variables
export JAVA_HOME=/data/data/com.termux/files/usr/opt/openjdk
export PATH=$JAVA_HOME/bin:$PATH
export ANDROID_HOME=$HOME/.android
export ANDROID_SDK_ROOT=$ANDROID_HOME/sdk

# 5. Add to bashrc for persistence
echo 'export JAVA_HOME=/data/data/com.termux/files/usr/opt/openjdk' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
echo 'export ANDROID_HOME=$HOME/.android' >> ~/.bashrc
echo 'export ANDROID_SDK_ROOT=$ANDROID_HOME/sdk' >> ~/.bashrc

# 6. Install buildozer
pip install buildozer cython

# 7. Navigate to project directory
cd ~/projects/AIStudioDownloadManager

# 8. Build debug APK (first time will download SDK/NDK - takes ~30 min)
buildozer android debug
```

## After First Setup (Daily Use)

```bash
# Navigate to project
cd ~/projects/AIStudioDownloadManager

# Build debug APK
buildozer android debug

# Build release APK
buildozer android release

# Clean and rebuild
buildozer clean
buildozer android debug
```

## Common Fixes

```bash
# If build fails, try with allow-download
buildozer android debug --allow-download

# If permission denied
termux-setup-storage

# If low on space
pkg clean
rm -rf ~/.cache/pip

# Reset buildozer
rm -rf .buildozer
buildozer android debug
```

## APK Location

After building, find your APK here:
```
bin/aistudiodownloadmanager-2.0.0-debug.apk
```

## Install APK

1. Transfer APK to phone (if built on PC)
2. Enable "Install from Unknown Sources" in Settings
3. Open APK file to install
