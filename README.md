# AI Studio Download Manager - Android Edition

A powerful download manager built with Kivy for Android compatibility.

## Features

- Multi-threaded downloads
- Pause/Resume support
- Queue management
- Speed limiting
- Metadata extraction
- Dark/Light theme support
- Material Design UI

## Requirements

- Python 3.9+
- Kivy 2.2.0+

## Project Structure

```
project/
├── main.py              # Main application entry point
├── config.py            # Configuration management
├── download_manager.py  # Download logic and workers
├── metadata_worker.py   # Metadata extraction
├── ui_styles.py         # UI styling and theming
├── utils.py             # Utility functions
├── buildozer.spec       # Buildozer configuration
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Building APK on Termux (Android Phone)

### Step 1: Install Termux

Download and install Termux from F-Droid (recommended) or Play Store.

### Step 2: Update Termux Packages

```bash
pkg update && pkg upgrade -y
```

### Step 3: Install Required Packages

```bash
pkg install -y python python-pip build-essential libffi openssl libxml2 libxslt jpeg png sqlite git
```

### Step 4: Install Buildozer

```bash
pip install buildozer cython
```

### Step 5: Install Java and Android SDK

```bash
pkg install -y openjdk-17
pkg install -y android-tools
```

### Step 6: Set Environment Variables

```bash
export JAVA_HOME=/data/data/com.termux/files/usr/opt/openjdk
export PATH=$JAVA_HOME/bin:$PATH
export ANDROID_HOME=$HOME/.android
export ANDROID_SDK_ROOT=$ANDROID_HOME/sdk
```

Add to your `.bashrc` or `.zshrc`:

```bash
echo 'export JAVA_HOME=/data/data/com.termux/files/usr/opt/openjdk' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
echo 'export ANDROID_HOME=$HOME/.android' >> ~/.bashrc
echo 'export ANDROID_SDK_ROOT=$ANDROID_HOME/sdk' >> ~/.bashrc
```

### Step 7: Clone or Copy Project

```bash
cd ~
mkdir -p projects
cd projects
# Copy your project files here or clone from git
```

### Step 8: Initialize Buildozer (First Time Only)

```bash
cd ~/projects/AIStudioDownloadManager
buildozer init
# This will create a default buildozer.spec (already provided)
```

### Step 9: Build Debug APK

```bash
buildozer android debug
```

### Step 10: Build Release APK

```bash
buildozer android release
```

## Important Notes for Termux

1. **Storage Access**: Termux needs storage permission:
   ```bash
   termux-setup-storage
   ```

2. **Memory**: Building APK requires significant RAM. Close other apps during build.

3. **First Build**: The first build downloads Android SDK/NDK (~2GB), which may take time.

4. **Build Time**: APK compilation can take 15-30 minutes on a phone.

5. **Build Output**: APK will be in the `bin/` directory.

## Alternative: Build on Linux/PC

If building on a phone is too slow, you can build on Linux:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3 python3-pip python3-venv build-essential libffi-dev libssl-dev libxml2-dev libxslt1-dev libjpeg-dev libpng-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install buildozer
pip install buildozer cython

# Build APK
buildozer android debug
```

## Troubleshooting

### Error: SDK/NDK not found
```bash
buildozer android debug --allow-download
```

### Error: Java not found
```bash
pkg install openjdk-17
```

### Error: Permission denied
```bash
termux-setup-storage
```

### Error: Out of memory
Close other apps and try again, or build on PC.

### Error: Build fails
Try cleaning the build:
```bash
buildozer clean
buildozer android debug
```

## Installing APK

After building, transfer the APK from `bin/` to your device and install:
- Enable "Install from Unknown Sources" in Android settings
- Open the APK file to install

## Development

To run the app on desktop for testing:

```bash
pip install kivy kivymd requests pillow
python main.py
```

## License

MIT License
