# AI-Powered Content Moderation System

A scalable, microservices-based content moderation system that uses AI to automatically detect and flag inappropriate text and image content in real-time.

## 🚀 Features

- **Text Moderation**: Uses NLP models to detect toxic language, hate speech, profanity, and threats
- **Image Moderation**: Uses computer vision to identify explicit content, violence, weapons, and inappropriate imagery
- **Microservices Architecture**: Modular design with separate services for text and image moderation
- **Real-Time Processing**: Handle content as it's submitted with fast response times
- **Scalable Design**: Built to handle increasing loads with horizontal scaling capabilities
- **API Gateway**: Centralized routing and request management
- **Database Integration**: Track moderation results and user statistics
- **Comprehensive Testing**: Full test coverage for all components
- **Free Tech Stack**: Built entirely with open-source and free-tier tools

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   API Gateway   │───▶│   Text Service  │
└─────────────────┘    │  (Port 8000)    │    │  (Port 8001)    │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Image Service  │
                       │  (Port 8002)    │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │    Database     │
                       │   (SQLite)      │
                       └─────────────────┘
```

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI (Python)
- **AI/ML Libraries**: 
  - Hugging Face Transformers (NLP)
  - OpenCV (Computer Vision)
  - TensorFlow/PyTorch
- **Database**: SQLite (with migration support)
- **Testing**: pytest with async support
- **Documentation**: OpenAPI/Swagger (auto-generated)
- **Containerization**: Docker (optional)
- **CI/CD**: GitHub Actions

## 📦 Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/AI-powered-content-Moderation-system.git
   cd AI-powered-content-Moderation-system
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python database/migrations/001_initial_schema.py
   ```

5. **Download required models** (optional - models download automatically on first use)
   ```bash
   python scripts/download_models.py
   ```

## 🚀 Running the Services

### Option 1: Run All Services Individually

**Terminal 1 - API Gateway**
```bash
cd api-gateway
python main.py
```

**Terminal 2 - Text Moderation Service**
```bash
cd text-moderation-service
python main.py
```

**Terminal 3 - Image Moderation Service**
```bash
cd image-moderation-service
python main.py
```

### Option 2: Using the Start Script
```bash
python scripts/start_services.py
```

### Option 3: Using Docker (Optional)
```bash
docker build -t content-moderation .
docker run -p 8000:8000 -p 8001:8001 -p 8002:8002 content-moderation
```

## 📖 API Documentation

Once the services are running, you can access the interactive API documentation:

- **API Gateway**: http://localhost:8000/docs
- **Text Service**: http://localhost:8001/docs  
- **Image Service**: http://localhost:8002/docs

## 🔌 API Usage Examples

### Text Moderation

```bash
# Moderate text content
curl -X POST "http://localhost:8000/api/v1/moderate/text" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "This is a sample message to moderate",
       "user_id": "user123",
       "content_id": "content456"
     }'
```

**Response:**
```json
{
  "is_appropriate": true,
  "confidence_score": 0.95,
  "flagged_categories": [],
  "processed_text": "this is a sample message to moderate",
  "user_id": "user123",
  "content_id": "content456"
}
```

### Image Moderation

```bash
# Moderate image content
curl -X POST "http://localhost:8000/api/v1/moderate/image" \
     -F "file=@/path/to/image.jpg" \
     -F "user_id=user123" \
     -F "content_id=image456"
```

**Response:**
```json
{
  "is_appropriate": true,
  "confidence_score": 0.85,
  "flagged_categories": [],
  "image_info": {
    "width": 1024,
    "height": 768,
    "format": "JPEG",
    "file_size_mb": 0.5
  },
  "user_id": "user123",
  "content_id": "image456"
}
```

### Batch Text Moderation

```bash
curl -X POST "http://localhost:8000/api/v1/moderate/text/batch" \
     -H "Content-Type: application/json" \
     -d '{
       "texts": ["Message 1", "Message 2", "Message 3"],
       "user_id": "user123"
     }'
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/text-moderation/
pytest tests/image-moderation/

# Run with coverage
pytest --cov=. --cov-report=html
```

## 📊 Monitoring and Analytics

### Health Checks

Check service health:
```bash
curl http://localhost:8000/health
```

### Service Status

Get detailed service status:
```bash
curl http://localhost:8000/api/v1/services/status
```

### Analytics

The system tracks moderation statistics in the database. You can query the database directly or extend the API to provide analytics endpoints.

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Service URLs
TEXT_SERVICE_URL=http://localhost:8001
IMAGE_SERVICE_URL=http://localhost:8002

# Database
DATABASE_PATH=moderation.db

# Model Settings
TORCH_DEVICE=auto  # auto, cpu, cuda
MODEL_CACHE_DIR=./models/cache

# API Settings
API_RATE_LIMIT=100  # requests per minute
MAX_FILE_SIZE_MB=10
MAX_TEXT_LENGTH=10000
```

### Customizing Moderation Categories

Edit the category lists in:
- `text-moderation-service/models/text_classifier.py`
- `image-moderation-service/models/image_classifier.py`

### Adjusting Thresholds

Modify confidence thresholds in the respective model files to fine-tune sensitivity.

## 📁 Project Structure

```
ai-content-moderation/
├── text-moderation-service/     # NLP-based text moderation
│   ├── models/                  # AI models for text analysis
│   ├── api/                     # Text moderation API endpoints
│   ├── utils/                   # Text preprocessing utilities
│   └── main.py                  # Service entry point
├── image-moderation-service/    # Computer vision image moderation
│   ├── models/                  # AI models for image analysis
│   ├── api/                     # Image moderation API endpoints
│   ├── utils/                   # Image preprocessing utilities
│   └── main.py                  # Service entry point
├── api-gateway/                 # Central API gateway
│   ├── routes/                  # Request routing logic
│   └── main.py                  # Gateway entry point
├── database/                    # Database components
│   ├── migrations/              # Database schema migrations
│   └── db.py                    # Database connection logic
├── tests/                       # Test suites
│   ├── text-moderation/         # Text moderation tests
│   └── image-moderation/        # Image moderation tests
├── docs/                        # Additional documentation
├── scripts/                     # Utility scripts
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🚀 Deployment

### Local Development
Follow the installation instructions above.

### Cloud Deployment (Free Tiers)

**Heroku:**
1. Create `Procfile`: `web: python api-gateway/main.py`
2. Deploy using Heroku CLI

**Google Cloud Platform:**
1. Use Cloud Run for serverless deployment
2. Configure environment variables in Cloud Console

**Fly.io:**
1. Install Fly CLI
2. Run `fly deploy`

### Docker Deployment

```bash
# Build image
docker build -t content-moderation .

# Run container
docker run -d -p 8000:8000 content-moderation
```

## 🔒 Security Considerations

- **Input Validation**: All inputs are validated and sanitized
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Authentication**: Add authentication for production use
- **HTTPS**: Use HTTPS in production
- **Content Logging**: Be mindful of privacy when logging content

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Hugging Face** for providing excellent pre-trained models
- **FastAPI** for the amazing web framework
- **OpenCV** for computer vision capabilities
- **The open-source community** for making this project possible

## 📞 Support

For questions, issues, or contributions:

- **Issues**: [GitHub Issues](https://github.com/your-username/AI-powered-content-Moderation-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/AI-powered-content-Moderation-system/discussions)
- **Email**: your-email@example.com

## 🗺️ Roadmap

- [ ] Add support for video content moderation
- [ ] Implement user reputation system
- [ ] Add multi-language support
- [ ] Create web dashboard for monitoring
- [ ] Add webhook notifications
- [ ] Implement custom model training pipeline
- [ ] Add Redis caching for improved performance
- [ ] Create mobile SDK
- [ ] Add A/B testing framework for model comparisons
