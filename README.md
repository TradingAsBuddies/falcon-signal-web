# falcon-signal-web

A container that runs a web-based front end for sangre-signal project. This is part of the [Falcon](https://github.com/TradingAsBuddies/falcon) project and provides a web-based interface for the [sangre-signal](https://github.com/anomalyco/sangre-signal) stock analysis tool. This containerized application provides a user-friendly web interface and API for analyzing stocks for various risk factors.

![Build and Test Docker Container](https://github.com/TradingAsBuddies/falcon-signal-web/actions/workflows/docker-build.yml/badge.svg)

## Features

- **Web Interface**: Clean, responsive web interface for stock analysis
- **API Endpoints**: RESTful API for programmatic access
- **Multiple Output Formats**: Text, JSON, CSV, Claude AI, Perplexity AI
- **Containerized**: Easy deployment with Docker and Docker Compose
- **Rate Limiting**: Built-in rate limiting and cache management
- **Health Monitoring**: System status and health checks

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Access to the sangre-signal source code (mounted as volume)

### Installation

#### Option 1: Using GitHub Container Registry

1. **Pull and run the container**:
   ```bash
   docker run -d -p 5000:5000 ghcr.io/tradingasbuddies/falcon-signal-web:latest
   ```

2. **Access the application**:
   - Web Interface: http://localhost:5000
   - API Status: http://localhost:5000/api/status

#### Option 2: Build from Source

1. **Clone the repository**:
   ```bash
   git clone https://github.com/TradingAsBuddies/falcon-signal-web.git
   cd falcon-signal-web
   ```

2. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Web Interface: http://localhost:5000
   - API Status: http://localhost:5000/api/status

### Development Mode

For development with live reloading:

```bash
# Install dependencies locally
pip install -r requirements.txt

# Run the Flask development server
python run.py
```

## Usage

### Web Interface

1. Open http://localhost:5000 in your browser
2. Enter stock tickers (e.g., AAPL, GOOG, MSFT)
3. Select output format
4. Click "Analyze" to view results

### API Endpoints

#### Analyze Stocks

**POST** `/api/analyze`

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": "AAPL,GOOG",
    "format": "json"
  }'
```

**GET** `/api/analyze`

```bash
curl "http://localhost:5000/api/analyze?tickers=AAPL&format=json"
```

#### System Status

**GET** `/api/status`

```bash
curl http://localhost:5000/api/status
```

### Output Formats

- **text**: Colored terminal output (default)
- **json**: Structured JSON data
- **csv**: Comma-separated values
- **claude**: AI-powered analysis (Claude)
- **perplexity**: AI-powered analysis (Perplexity)

## Configuration

### Environment Variables

- `FLASK_ENV`: Set to `development` for debug mode (default: production)
- `PORT`: Web server port (default: 5000)
- `SECRET_KEY`: Flask secret key (change in production)

### Docker Compose Options

#### Basic Deployment
```bash
docker-compose up --build
```

#### Production with Nginx
```bash
docker-compose --profile production up --build
```

#### Background Service
```bash
docker-compose up -d --build
```

#### View Logs
```bash
docker-compose logs -f web
```

#### Stop Service
```bash
docker-compose down
```

## Project Structure

```
sangre-signal-web/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── routes.py            # Web routes and API endpoints
│   ├── static/              # CSS, JS files
│   └── templates/           # HTML templates
├── Dockerfile               # Container definition
├── docker-compose.yml       # Container orchestration
├── nginx.conf              # Nginx configuration (production)
├── requirements.txt        # Python dependencies
├── run.py                  # Application entry point
└── README.md               # This file
```

## Dependencies

### Web Framework
- Flask 2.3.3
- Flask-WTF 1.1.1
- WTForms 3.0.1

### Production Server
- Gunicorn 20.1.0

### Core Module
- sangre-signal (installed from local source)

### Additional
- Requests 2.31.0
- python-dotenv 1.0.0

## Data Sources

The application uses the same data sources as sangre-signal:

- **Yahoo Finance**: Real-time stock data, prices, volumes
- **FinViz**: Additional stock metrics and executive information

## Rate Limiting & Caching

- Built-in rate limiting for Yahoo Finance API
- Persistent caching to reduce API calls
- Cache TTL: Configurable (default: 1 hour)
- Rate limit status available via `/status` endpoint

## Security Features

- CSRF protection on all forms
- Input validation and sanitization
- Rate limiting to prevent abuse
- Secure headers (via Flask security best practices)

## Monitoring & Health

### Health Checks

- Container health check: `/status`
- Application health: `/api/status`
- Nginx health: `/health` (production mode)

### Logging

- Application logs available via Docker
- Error tracking and reporting
- Request logging (configurable)

## Troubleshooting

### Common Issues

1. **sangre-signal module not found**
   - Ensure the sangre-signal source is mounted correctly
   - Check the volume path in docker-compose.yml

2. **Rate limiting errors**
   - Check status page for current rate limits
   - Wait for rate limit reset if needed

3. **Container won't start**
   - Check Docker logs: `docker-compose logs web`
   - Verify all dependencies are installed

### Debug Mode

Enable debug mode for development:

```bash
# Set environment variable
export FLASK_ENV=development

# Or modify docker-compose.yml
environment:
  - FLASK_ENV=development
```

## Production Deployment

### Security Considerations

1. Change default secret key
2. Use HTTPS (configure nginx.conf)
3. Set up proper firewall rules
4. Monitor logs and metrics
5. Regular security updates

### Performance Optimization

1. Use nginx reverse proxy
2. Enable caching headers
3. Monitor resource usage
4. Scale horizontally if needed

### Backup & Recovery

- Persistent cache storage in `/app/data`
- Regular database backups
- Container image versioning

## API Reference

### Response Format

All API responses follow this structure:

```json
{
  "success": true|false,
  "data": {...}|null,
  "error": "Error message"|null
}
```

### Error Codes

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `500`: Internal Server Error (module not available, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker Compose
5. Submit a pull request

## License

This project maintains the same license as sangre-signal.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review Docker logs
3. Open an issue on GitHub
4. Check sangre-signal documentation

## Version History

- **v1.0.0**: Initial release with web interface and API
- **v1.1.0**: Added nginx support and production optimizations
- **v1.2.0**: Enhanced error handling and monitoring