# Recipe Generator API

AI-powered recipe generator with intelligent S3 caching and recipe matching.

## 🏗️ Project Structure
recipe-generator/
├── modal_app/
│ ├── init.py # Package initialization
│ ├── main.py # FastAPI app and Modal setup
│ ├── models.py # Pydantic data models
│ ├── recipe_model.py # AI model and generation logic
│ ├── s3_manager.py # S3 operations
│ └── recipe_matcher.py # Recipe matching algorithms
├── requirements.txt # Python dependencies
├── deploy.sh # Deployment script
├── dev.sh # Development server script
└── README.md # This file