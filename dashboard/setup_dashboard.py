#!/usr/bin/env python
"""
Django Dashboard Initialization Script
Automates the setup process for the Content Moderation Dashboard
"""

import os
import sys
import subprocess
import django
from pathlib import Path

def run_command(command, description):
    """Run a system command with error handling"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_django():
    """Initialize Django project"""
    print("🚀 Starting Django Content Moderation Dashboard Setup...")
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = ".\\venv\\Scripts\\Activate.ps1"
        pip_cmd = ".\\venv\\Scripts\\pip"
        python_cmd = ".\\venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Install dependencies
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """DJANGO_SECRET_KEY=django-insecure-content-moderation-dashboard-secret-key-12345
DATABASE_URL=sqlite:///./db.sqlite3
DEBUG=True"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with default settings")
    
    # Create static directory
    static_dir = Path("static")
    if not static_dir.exists():
        static_dir.mkdir()
        print("✅ Created static directory")
    
    # Run migrations
    if not run_command(f"{python_cmd} manage.py makemigrations", "Creating database migrations"):
        return False
    
    if not run_command(f"{python_cmd} manage.py migrate", "Applying database migrations"):
        return False
    
    # Create superuser
    print("\n👤 Creating admin user...")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
        django.setup()
        
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            print("✅ Created admin user (username: admin, password: admin123)")
        else:
            print("ℹ️  Admin user already exists")
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
    
    # Collect static files
    if not run_command(f"{python_cmd} manage.py collectstatic --noinput", "Collecting static files"):
        print("⚠️  Static files collection failed, but this is not critical")
    
    print("\n🎉 Django Dashboard setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start the dashboard: python manage.py runserver 8080")
    print("2. Visit: http://localhost:8080")
    print("3. Admin panel: http://localhost:8080/admin")
    print("4. Login with username: admin, password: admin123")
    print("\n🔧 Make sure your moderation services are running:")
    print("   - API Gateway: http://localhost:8000")
    print("   - Text Service: http://localhost:8001") 
    print("   - Image Service: http://localhost:8002")
    
    return True

if __name__ == "__main__":
    if setup_django():
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
