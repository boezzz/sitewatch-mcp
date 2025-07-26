# SiteWatch Full-Stack Application

A modern full-stack website monitoring system with AI-powered analysis and real-time chat interface.

## Features

- **Chat Interface**: Simple conversation-based setup for monitoring jobs
- **Real-time Updates**: WebSocket-powered live updates of monitoring results
- **AI-Powered Analysis**: Intelligent URL generation and content summarization
- **Scheduled Monitoring**: Automated daily monitoring with customizable schedules
- **Change Detection**: Content hash-based change detection with detailed analysis
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS

## Architecture

### Backend (FastAPI)
- **FastAPI** web framework with async support
- **SQLite** database with SQLAlchemy ORM
- **WebSocket** support for real-time communication
- **Background scheduler** for automated monitoring
- **Tavily API** integration for web content extraction
- **OpenAI API** integration for intelligent analysis

### Frontend (React)
- **React 18** with functional components and hooks
- **Tailwind CSS** for styling
- **WebSocket** client for real-time updates
- **Responsive design** with chat and sidebar layout

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key (optional but recommended)

### 1. Set up the Backend

```bash
cd src/backend

# Install Python dependencies
pip install -r requirements.txt

# Set OpenAI API key (optional)
export OPENAI_API_KEY="your-openai-api-key-here"

# Run the backend
python run.py
```

The backend will start on `http://localhost:8000`

### 2. Set up the Frontend

```bash
cd src/frontend

# Install Node.js dependencies
npm install

# Start the development server
npm start
```

The frontend will start on `http://localhost:3000`

### 3. Start Using SiteWatch

1. Open `http://localhost:3000` in your browser
2. Type a monitoring request in the chat, for example:
   - "Monitor AI startup job postings"
   - "Track product updates for tech companies"
   - "Watch for FDA drug approvals"
3. The system will create a monitoring job and start tracking changes
4. View scheduled jobs in the sidebar and monitor real-time updates

## API Endpoints

### REST API
- `GET /api/chat/messages` - Get chat messages
- `GET /api/jobs` - Get monitoring jobs
- `GET /api/jobs/{job_id}/results` - Get job results
- `POST /api/jobs/{job_id}/toggle` - Toggle job status
- `DELETE /api/jobs/{job_id}` - Delete job
- `GET /api/stats` - Get application statistics

### WebSocket
- `ws://localhost:8000/ws` - Real-time communication

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - OpenAI API key for AI features (optional)
- `DATABASE_URL` - Database URL (defaults to SQLite)

### Customization

#### Backend
- Modify `src/backend/services/monitoring.py` for custom monitoring logic
- Adjust `src/backend/services/scheduler.py` for different scheduling behavior
- Update `src/backend/models.py` to add new database fields

#### Frontend
- Customize UI in `src/frontend/src/components/`
- Modify styling in `src/frontend/src/index.css`
- Add new features to `src/frontend/src/App.js`

## Development

### Backend Development

```bash
cd src/backend

# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
python main.py

# Access API docs at http://localhost:8000/docs
```

### Frontend Development

```bash
cd src/frontend

# Install dependencies
npm install

# Start development server with hot reload
npm start

# Build for production
npm run build
```

### Database

The application uses SQLite by default. The database file `sitewatch.db` will be created automatically in the backend directory.

To reset the database, simply delete the `sitewatch.db` file and restart the backend.

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   - Check that backend is running on port 8000
   - Ensure no firewall blocking the connection

2. **OpenAI features not working**
   - Verify `OPENAI_API_KEY` environment variable is set
   - Check that you have sufficient API credits

3. **Frontend can't connect to backend**
   - Ensure backend is running on `http://localhost:8000`
   - Check the proxy setting in `package.json`

4. **Monitoring jobs not running**
   - Check backend logs for scheduler errors
   - Verify job is marked as active in the database

### Logs

Backend logs are printed to console when running with `python run.py`.

## Production Deployment

### Backend
- Use a production WSGI server like Gunicorn
- Configure environment variables for production
- Use PostgreSQL or MySQL for production database
- Set up proper logging and monitoring

### Frontend
- Build with `npm run build`
- Serve static files with nginx or similar
- Configure proper CORS settings for production domain

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the API documentation at `http://localhost:8000/docs`
- Create an issue on the project repository 