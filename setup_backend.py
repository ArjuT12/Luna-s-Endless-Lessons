#!/usr/bin/env python3
"""
Setup script for Luna's Endless Lesson Backend Integration
This script helps set up the backend API and test the connection
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_env_file():
    """Create .env file for backend configuration"""
    env_file = Path("backend/.env")
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("\n🔧 Creating .env file...")
    mongo_uri = input("Enter MongoDB URI (or press Enter for local MongoDB): ").strip()
    if not mongo_uri:
        mongo_uri = "mongodb://localhost:27017/"
    
    env_content = f"""# MongoDB Configuration
MONGO_URI={mongo_uri}

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def test_backend_connection():
    """Test connection to backend API"""
    print("\n🔌 Testing backend connection...")
    try:
        import requests
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is running")
            return True
        else:
            print(f"❌ Backend API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend API is not running")
        print("💡 Start the backend with: python backend/app.py")
        return False
    except ImportError:
        print("❌ requests library not installed")
        return False

def test_game_integration():
    """Test game integration with API"""
    print("\n🎮 Testing game integration...")
    try:
        from api_client import test_api_connection
        if test_api_connection():
            print("✅ Game API integration working")
            return True
        else:
            print("❌ Game API integration failed")
            return False
    except ImportError as e:
        print(f"❌ Failed to import API client: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Luna's Endless Lesson Backend Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Create .env file
    if not create_env_file():
        return False
    
    print("\n📋 Setup Summary:")
    print("✅ Python version compatible")
    print("✅ Requirements installed")
    print("✅ Environment file created")
    
    print("\n🔧 Next Steps:")
    print("1. Start MongoDB (if using local instance)")
    print("2. Start the backend API: python backend/app.py")
    print("3. Run the game: python main.py")
    
    print("\n🧪 Testing:")
    if test_backend_connection():
        test_game_integration()
        
        print("\n🔬 Running comprehensive API integration test...")
        try:
            from test_api_integration import test_api_integration
            if test_api_integration():
                print("✅ All API tests passed!")
            else:
                print("❌ Some API tests failed - check your setup")
        except ImportError:
            print("⚠️ Could not run API integration test")
        except Exception as e:
            print(f"⚠️ API integration test error: {e}")
    
    print("\n✨ Setup complete! Happy gaming!")
    print("\n🎮 To start playing:")
    print("   1. Start backend: python backend/app.py")
    print("   2. Run game: python main.py")
    print("   3. Test API: python test_api_integration.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
