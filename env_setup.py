"""
Environment setup script for Kenyan Real Estate AI Agent
Run this script to create the .env file with the proper configuration
"""

def create_env_file():
    """Create .env file with default configuration"""
    
    env_content = """# Kenyan Real Estate AI Agent Configuration

# Together AI Configuration
TOGETHER_API_KEY=0ead0c7716c61be64bc13c4a0aea90147e4ddb56a7ac5d437fe15f57b758ea3f
TOGETHER_MODEL=deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Knowledge Base Configuration
KNOWLEDGE_BASE_PATH=./knowledgebase
MAX_CONTEXT_LENGTH=4000

# Application Settings
APP_NAME=Kenyan Real Estate AI Agent
APP_VERSION=1.0.0
CORS_ORIGINS=["*"]
"""

    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("📝 You can modify the settings in the .env file as needed.")
        print("🔑 Your Together AI API key is already configured.")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

if __name__ == "__main__":
    print("🏠 Setting up Kenyan Real Estate AI Agent environment...")
    print("=" * 50)
    
    success = create_env_file()
    
    if success:
        print("\n✨ Setup complete! You can now run the application with:")
        print("   python run.py")
        print("\n🌐 The API will be available at: http://localhost:8000")
        print("📚 Documentation will be at: http://localhost:8000/docs")
    else:
        print("\n❌ Setup failed. Please create the .env file manually.")
