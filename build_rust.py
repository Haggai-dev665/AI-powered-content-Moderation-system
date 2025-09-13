#!/usr/bin/env python3
"""
Build script for Rust moderation library with Python bindings
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        print(f"✓ Command completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Command failed: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False

def build_rust_library():
    """Build the Rust library"""
    print("Building Rust moderation library...")
    
    # Change to rust-moderation directory
    rust_dir = Path(__file__).parent / "rust-moderation"
    
    if not rust_dir.exists():
        print("Error: rust-moderation directory not found")
        return False
    
    # Build the library
    if not run_command("cargo build --release", cwd=rust_dir):
        print("Failed to build Rust library")
        return False
    
    # Check if the library was built
    lib_file = rust_dir / "target" / "release" / "librust_moderation.so"
    if not lib_file.exists():
        # Try different extensions
        lib_file = rust_dir / "target" / "release" / "rust_moderation.dll"
        if not lib_file.exists():
            lib_file = rust_dir / "target" / "release" / "librust_moderation.dylib"
    
    if lib_file.exists():
        print(f"✓ Rust library built: {lib_file}")
        
        # Copy to a location where Python can find it
        target_dir = Path(__file__).parent / "text-moderation-service" / "rust_lib"
        target_dir.mkdir(exist_ok=True)
        
        # Copy the library file
        shutil.copy2(lib_file, target_dir / lib_file.name)
        print(f"✓ Library copied to {target_dir}")
        
        return True
    else:
        print("✗ Rust library file not found after build")
        return False

def install_rust():
    """Install Rust if not available"""
    try:
        subprocess.run(["rustc", "--version"], check=True, capture_output=True)
        print("✓ Rust is already installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Rust not found. Installing...")
        
        # Install Rust using rustup
        install_cmd = "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"
        if run_command(install_cmd):
            # Source the cargo environment
            cargo_env = os.path.expanduser("~/.cargo/env")
            if os.path.exists(cargo_env):
                os.system(f"source {cargo_env}")
            print("✓ Rust installed successfully")
            return True
        else:
            print("✗ Failed to install Rust")
            return False

def main():
    """Main build function"""
    print("=== Rust Moderation Library Build Script ===")
    
    # Check if Rust is installed
    if not install_rust():
        print("Cannot proceed without Rust")
        return False
    
    # Build the Rust library
    if not build_rust_library():
        print("Build failed")
        return False
    
    print("\n=== Build completed successfully ===")
    print("The Rust moderation library is now available for use with Python")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)