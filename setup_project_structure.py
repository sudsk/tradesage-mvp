# setup_project_structure.py - Script to set up proper project structure
"""
Script to ensure proper project structure and file placement
"""
import os
import sys

def create_project_structure():
    """Create the necessary directories and files."""
    
    print("📁 Creating project structure...")
    
    # Create directories if they don't exist
    directories = [
        "scripts",
        "app",
        "app/database",
        "app/agents",
        "app/agents/hypothesis_agent",
        "app/agents/research_agent",
        "app/agents/contradiction_agent",
        "app/agents/synthesis_agent",
        "app/agents/alert_agent",
        "app/tools",
        "app/utils",
        "frontend",
        "frontend/src",
        "frontend/src/api",
        "frontend/src/components",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"  ✅ Created directory: {directory}")
    
    # Create __init__.py files where needed
    init_files = [
        "app/__init__.py",
        "app/database/__init__.py",
        "app/agents/__init__.py",
        "app/tools/__init__.py",
        "app/utils/__init__.py",
        "scripts/__init__.py"
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# This file makes Python treat the directory as a package\n")
            print(f"  ✅ Created: {init_file}")
    
    # Check and report existing files
    important_files = [
        "app/main.py",
        "app/graph.py",
        "app/agent.py",
        "requirements.txt",
        "pyproject.toml",
        "Makefile",
        "README.md"
    ]
    
    print("\n📋 Checking important files:")
    for file in important_files:
        if os.path.exists(file):
            print(f"  ✅ Found: {file}")
        else:
            print(f"  ⚠️  Missing: {file}")
    
    print("\n🎉 Project structure setup complete!")
    print("You can now place the init_db.py file in the scripts/ directory")

if __name__ == "__main__":
    create_project_structure()
