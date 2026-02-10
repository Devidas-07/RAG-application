#!/usr/bin/env python3
"""
Setup and startup helper for RAG Q&A System
Run this script to set up and verify your system before starting the application
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def print_step(step_num, title):
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {title}")
    print('='*60)

def print_success(message):
    print(f"✓ {message}")

def print_error(message):
    print(f"✗ {message}")

def print_warning(message):
    print(f"⚠ {message}")

def check_command(cmd, description):
    """Check if a command exists"""
    try:
        result = subprocess.run(f"{cmd} --version", shell=True, capture_output=True, timeout=5)
        if result.returncode == 0:
            print_success(f"{description} is installed")
            return True
    except:
        pass
    print_error(f"{description} is not installed")
    return False

def check_service_running(url, service_name):
    """Check if a service is running"""
    try:
        import requests
        response = requests.get(url, timeout=3)
        print_success(f"{service_name} is running")
        return True
    except:
        print_error(f"{service_name} is not responding at {url}")
        return False

def create_env_file():
    """Create .env file from example"""
    print_step(1, "Creating Environment File")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_warning(".env already exists")
        return True
    
    if env_example.exists():
        env_file.write_text(env_example.read_text())
        print_success(".env created from .env.example")
        return True
    else:
        print_error(".env.example not found")
        return False

def check_prerequisites():
    """Check all prerequisites"""
    print_step(2, "Checking Prerequisites")
    
    all_good = True
    
    # Check Python
    if not check_command("python", "Python 3"):
        all_good = False
    
    # Check Docker
    if not check_command("docker", "Docker"):
        all_good = False
        print_warning("Docker is needed for Elasticsearch and MinIO")
    
    # Check Ollama
    if not check_command("ollama", "Ollama"):
        all_good = False
        print_warning("Ollama needs to be installed and running locally")
    else:
        # Check if Ollama service is accessible
        check_service_running("http://localhost:11434/api/tags", "Ollama API")
    
    return all_good

def setup_virtual_env():
    """Set up Python virtual environment"""
    print_step(3, "Setting up Virtual Environment")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_warning("Virtual environment already exists")
    else:
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print_success("Virtual environment created")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to create virtual environment: {e}")
            return False
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_step(4, "Installing Python Dependencies")
    
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print_error("requirements.txt not found")
        return False
    
    try:
        # Determine pip command based on OS
        if sys.platform == "win32":
            pip_cmd = "venv\\Scripts\\pip"
        else:
            pip_cmd = "venv/bin/pip"
        
        subprocess.run(
            f"{pip_cmd} install -r requirements.txt",
            shell=True,
            check=True
        )
        print_success("Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

def start_services():
    """Start Docker services"""
    print_step(5, "Starting Docker Services")
    
    try:
        # Check if docker is running
        subprocess.run("docker ps", shell=True, capture_output=True, check=True)
    except:
        print_error("Docker is not running. Please start Docker Desktop.")
        return False
    
    try:
        print("Starting Elasticsearch and MinIO...")
        subprocess.run(
            "docker-compose up -d elasticsearch minio",
            shell=True,
            check=True
        )
        print_success("Docker services started")
        
        # Wait for services to be ready
        print("Waiting for services to be ready (30 seconds)...")
        time.sleep(30)
        
        # Check if services are running
        check_service_running("http://localhost:9200", "Elasticsearch")
        check_service_running("http://localhost:9000", "MinIO")
        
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start Docker services: {e}")
        return False

def verify_ollama_model():
    """Verify Ollama has the required model"""
    print_step(6, "Verifying Ollama Model")
    
    try:
        result = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
        
        if "gemma:4b" in result.stdout:
            print_success("gemma:4b model is available")
            return True
        else:
            print_warning("gemma:4b model not found locally")
            print("Pulling gemma:4b model (this may take a while)...")
            
            pull_result = subprocess.run(
                "ollama pull gemma:4b",
                shell=True,
                timeout=600
            )
            
            if pull_result.returncode == 0:
                print_success("gemma:4b model pulled successfully")
                return True
            else:
                print_error("Failed to pull gemma:4b model")
                return False
    
    except Exception as e:
        print_error(f"Error checking Ollama model: {e}")
        return False

def start_ollama():
    """Start Ollama if not running"""
    print_step(7, "Verifying Ollama Service")
    
    try:
        # Try to connect to Ollama
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            print_success("Ollama is already running")
            return True
    except:
        print_warning("Ollama is not responding")
    
    print("Please run Ollama in a separate terminal:")
    print("  ollama serve\n")
    
    # Wait for user to start Ollama
    max_wait = 60
    for i in range(max_wait):
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                print_success("Ollama is now running")
                return True
        except:
            pass
        
        if i > 0 and i % 10 == 0:
            print(f"  Still waiting... ({max_wait - i}s remaining)")
        time.sleep(1)
    
    print_error("Ollama is still not running")
    return False

def print_next_steps():
    """Print next steps"""
    print_step(8, "Next Steps")
    
    print("\nTo start the RAG Q&A System:\n")
    
    if sys.platform == "win32":
        print("1. Activate virtual environment:")
        print("   venv\\Scripts\\activate\n")
    else:
        print("1. Activate virtual environment:")
        print("   source venv/bin/activate\n")
    
    print("2. Start the FastAPI application:")
    print("   uvicorn main:app --host 0.0.0.0 --port 8000 --reload\n")
    
    print("3. Access the system:")
    print("   - API: http://localhost:8000")
    print("   - Documentation: http://localhost:8000/docs")
    print("   - MinIO Console: http://localhost:9001")
    print("   - Elasticsearch: http://localhost:9200\n")
    
    print("4. Test the system:")
    print("   python test_rag.py\n")

def main():
    """Main setup function"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  RAG Q&A System - Setup Assistant".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝\n")
    
    steps = [
        (create_env_file, "Creating environment file"),
        (check_prerequisites, "Checking prerequisites"),
        (setup_virtual_env, "Setting up virtual environment"),
        (install_dependencies, "Installing dependencies"),
        (start_services, "Starting Docker services"),
        (verify_ollama_model, "Verifying Ollama model"),
        (start_ollama, "Verifying Ollama service"),
    ]
    
    for step_func, description in steps:
        try:
            if not step_func():
                print_error(f"Failed at: {description}")
                print("\nPlease fix the above issues and run this script again.")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n\nSetup cancelled by user.")
            sys.exit(0)
        except Exception as e:
            print_error(f"Unexpected error during {description}: {e}")
            sys.exit(1)
    
    print_success("All setup steps completed successfully!")
    print_next_steps()

if __name__ == "__main__":
    main()
