import os
from dotenv import load_dotenv

# Find and load .env file if present
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

for dir_path in [parent_dir, current_dir]:
    env_file = os.path.join(dir_path, '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)

if 'GOOGLE_API_KEY' in os.environ and 'GEMINI_API_KEY' not in os.environ:
    os.environ['GEMINI_API_KEY'] = os.environ['GOOGLE_API_KEY']

# Import and expose root_agent from the orchestrator agent
from src.agents.orchestrator.agent import root_agent
