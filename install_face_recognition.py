#!/usr/bin/env python3
"""
Installation script for face recognition dependencies
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    print("🚀 Installing Face Recognition Dependencies...")
    print("=" * 50)
    
    # Required packages for face recognition
    packages = [
        "deepface==0.0.79",
        "tensorflow==2.13.0",
        "opencv-python==4.8.1.78",
        "Pillow==10.0.1",
        "numpy==1.24.3"
    ]
    
    failed_packages = []
    
    for package in packages:
        print(f"\n📦 Installing {package}...")
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n" + "=" * 50)
    
    if failed_packages:
        print("❌ Some packages failed to install:")
        for package in failed_packages:
            print(f"   - {package}")
        print("\n💡 Try installing them manually:")
        print("   pip install deepface tensorflow opencv-python")
    else:
        print("✅ All face recognition dependencies installed successfully!")
        print("\n🎉 You can now use real face verification!")
        print("\n📝 Note: On first use, DeepFace will download AI models (~100MB)")
    
    print("\n🔧 To test the installation, run:")
    print("   python -c \"from deepface import DeepFace; print('DeepFace is ready!')\"")

if __name__ == "__main__":
    main()