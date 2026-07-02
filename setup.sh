#!/bin/bash
# AI Studio Download Manager - Build Script for Android/Termux

set -e

echo "=========================================="
echo "AI Studio Download Manager - Build Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_status() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Termux
check_termux() {
    if [ -d "/data/data/com.termux" ]; then
        print_status "Detected Termux environment"
        IS_TERMUX=true
    else
        print_status "Running in standard Linux environment"
        IS_TERMUX=false
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."

    if [ "$IS_TERMUX" = true ]; then
        pkg update -y
        pkg upgrade -y
        pkg install -y python python-pip build-essential libffi openssl libxml2 libxslt jpeg png sqlite git openjdk-17 android-tools
    else
        # Ubuntu/Debian
        sudo apt update
        sudo apt install -y git zip unzip openjdk-17-jdk python3 python3-pip python3-venv build-essential libffi-dev libssl-dev libxml2-dev libxslt1-dev libjpeg-dev libpng-dev
    fi

    print_success "Dependencies installed"
}

# Setup Python environment
setup_python() {
    print_status "Setting up Python environment..."

    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate virtual environment
    if [ "$IS_TERMUX" = false ]; then
        source venv/bin/activate
    fi

    # Install Python packages
    pip install --upgrade pip
    pip install buildozer cython kivy kivymd requests pillow

    print_success "Python environment ready"
}

# Setup Android SDK
setup_android() {
    print_status "Setting up Android SDK..."

    export JAVA_HOME="/data/data/com.termux/files/usr/opt/openjdk"
    export PATH=$JAVA_HOME/bin:$PATH
    export ANDROID_HOME=$HOME/.android
    export ANDROID_SDK_ROOT=$ANDROID_HOME/sdk

    print_success "Android SDK paths configured"
}

# Build APK
build_apk() {
    print_status "Building APK..."

    local build_type="${1:-debug}"

    # Clean previous build
    if [ -d ".buildozer" ]; then
        print_status "Cleaning previous build..."
        rm -rf .buildozer android sdk build
    fi

    # Build
    if [ "$build_type" = "release" ]; then
        print_status "Building RELEASE APK..."
        buildozer android release
    else
        print_status "Building DEBUG apk..."
        buildozer android debug
    fi

    print_success "Build completed!"
    print_status "APK location: bin/*.apk"
}

# Run on desktop for testing
run_desktop() {
    print_status "Running on desktop..."
    python main.py
}

# Show help
show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install    Install all dependencies"
    echo "  setup      Setup Python environment"
    echo "  android    Setup Android SDK paths"
    echo "  build      Build debug APK"
    echo "  release    Build release APK"
    echo "  run        Run on desktop (for testing)"
    echo "  clean      Clean build artifacts"
    echo "  all        Full setup and build"
    echo "  help       Show this help message"
}

# Clean build artifacts
clean() {
    print_status "Cleaning build artifacts..."
    rm -rf .buildozer android sdk build bin dist __pycache__ *.pyc .egg-info
    print_success "Clean complete"
}

# Main script
main() {
    check_termux

    case "${1:-help}" in
        install)
            install_dependencies
            ;;
        setup)
            setup_python
            ;;
        android)
            setup_android
            ;;
        build)
            build_apk debug
            ;;
        release)
            build_apk release
            ;;
        run)
            run_desktop
            ;;
        clean)
            clean
            ;;
        all)
            install_dependencies
            setup_python
            setup_android
            build_apk debug
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Run main function with arguments
main "$@"
