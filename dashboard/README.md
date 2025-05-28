# Django Content Moderation Dashboard

A beautiful, modern web interface for the AI-powered Content Moderation System. This dashboard provides user authentication, API key management, real-time testing, analytics, and comprehensive documentation.

## Features

### 🔐 Authentication & User Management
- User registration and login system
- API key generation and management
- User profiles with usage tracking
- Secure session management

### 🧪 Interactive Testing Interface
- Real-time text moderation testing
- Image upload and moderation testing
- Instant results with confidence scores
- Processing time metrics

### 📊 Analytics & Insights
- Beautiful charts and visualizations
- Daily activity tracking
- Content category breakdown
- AI-powered insights and recommendations
- Performance metrics and health scores

### 📚 API Documentation
- Interactive API documentation
- Code examples in multiple languages
- SDK information and downloads
- Error handling guides

### 🎨 Modern UI/UX
- Responsive design with Bootstrap 5
- Beautiful gradients and animations
- Dark/light theme support
- Mobile-friendly interface

## Quick Start

### 1. Automated Setup
```bash
cd dashboard
python setup_dashboard.py
```

### 2. Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Unix/Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
echo "DJANGO_SECRET_KEY=your-secret-key-here" > .env
echo "DEBUG=True" >> .env

# Create database
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver 8080
```

## Configuration

### Environment Variables (.env)
```env
DJANGO_SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./db.sqlite3
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Settings
The dashboard is configured to work with the moderation services running on:
- API Gateway: `http://localhost:8000`
- Text Service: `http://localhost:8001`
- Image Service: `http://localhost:8002`

To change these URLs, modify `dashboard/settings.py`:
```python
MODERATION_SERVICES = {
    'API_GATEWAY': 'http://localhost:8000',
    'TEXT_SERVICE': 'http://localhost:8001',
    'IMAGE_SERVICE': 'http://localhost:8002',
}
```

## Usage

### 1. Start the Dashboard
```bash
cd dashboard
python manage.py runserver 8080
```

### 2. Access the Interface
- **Main Dashboard**: http://localhost:8080
- **Admin Panel**: http://localhost:8080/admin
- **API Documentation**: http://localhost:8080/documentation

### 3. User Registration
1. Visit the homepage
2. Click "Register" to create an account
3. Fill in your details and submit
4. Your API key will be automatically generated

### 4. Testing Moderation
1. Log in to your account
2. Navigate to "Test Moderation"
3. Enter text or upload an image
4. View real-time results and metrics

### 5. View Analytics
1. Go to the "Analytics" section
2. View charts and insights
3. Track your usage patterns
4. Monitor content quality

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout

### User Management
- `GET /api/profile/` - Get user profile
- `POST /api/profile/` - Regenerate API key

### Analytics
- `GET /api/stats/` - Get user statistics
- `GET /api/analytics/?chart=overview` - Overview charts
- `GET /api/analytics/?chart=daily` - Daily activity
- `GET /api/analytics/?chart=categories` - Category breakdown
- `GET /api/health/` - System health and insights

### Moderation Data
- `GET /api/moderation-requests/` - List moderation requests
- `GET /api/moderation-requests/recent/` - Recent requests
- `GET /api/usage-logs/` - API usage logs

## Models

### UserProfile
- User account extension with API key
- Usage tracking and limits
- Account status management

### ModerationRequest
- Stores all moderation requests
- Content type (text/image)
- Results and confidence scores
- Processing metrics

### APIUsageLog
- Detailed API call logging
- Request/response tracking
- Performance monitoring

### SystemStats
- System-wide statistics
- Performance metrics
- Health monitoring

## Testing

### Unit Tests
```bash
python manage.py test
```

### Integration Tests
```bash
python test_integration.py
```

### Load Testing
```bash
# Install locust first
pip install locust

# Run load tests
locust -f load_tests.py --host=http://localhost:8080
```

## Deployment

### Development
```bash
python manage.py runserver 8080
```

### Production with Gunicorn
```bash
pip install gunicorn
gunicorn dashboard.wsgi:application --bind 0.0.0.0:8080
```

### Docker Deployment
```bash
# Build image
docker build -t moderation-dashboard .

# Run container
docker run -p 8080:8080 moderation-dashboard
```

### Environment Setup
For production, ensure you:
1. Set `DEBUG=False`
2. Use a strong `SECRET_KEY`
3. Configure proper database (PostgreSQL recommended)
4. Set up static file serving
5. Configure HTTPS
6. Set proper `ALLOWED_HOSTS`

## Security

### Best Practices
- CSRF protection enabled
- Secure cookie settings
- SQL injection protection
- XSS protection
- Secure password hashing

### API Security
- Authentication required for all API endpoints
- Rate limiting implemented
- API key rotation supported
- Request logging and monitoring

## Troubleshooting

### Common Issues

#### "No module named 'django'"
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Unix/Linux

# Install dependencies
pip install -r requirements.txt
```

#### "CSRF verification failed"
- Ensure CSRF tokens are included in forms
- Check that `django.middleware.csrf.CsrfViewMiddleware` is enabled

#### "Static files not found"
```bash
# Collect static files
python manage.py collectstatic

# Or create static directory
mkdir static
```

#### Database errors
```bash
# Reset database
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Service Integration Issues

#### Services not responding
1. Check if moderation services are running:
   ```bash
   # Test service health
   curl http://localhost:8000/health
   curl http://localhost:8001/health  
   curl http://localhost:8002/health
   ```

2. Start missing services:
   ```bash
   # Start all services
   cd ../scripts
   python start_services.py
   ```

#### API connection errors
- Verify service URLs in settings
- Check firewall and network connectivity
- Ensure services are bound to correct ports

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide

## Roadmap

### Upcoming Features
- [ ] Real-time notifications
- [ ] Advanced filtering and search
- [ ] Bulk content processing
- [ ] Custom moderation rules
- [ ] Team collaboration features
- [ ] Advanced reporting
- [ ] Webhook integration
- [ ] Multi-language support
