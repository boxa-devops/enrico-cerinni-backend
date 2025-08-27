# Development Guide

## 🚀 Quick Start

### Backend Only
```bash
# Test the backend setup
./test-backend.sh

# Or manually:
docker-compose up --build
```

### Full Stack Development
```bash
# Start all services (backend + frontend + database)
docker-compose -f docker-compose.full.yml up --build
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Alembic Not Running Uvicorn
**Problem**: The container starts alembic but doesn't proceed to uvicorn.

**Solution**: 
- Check the startup script logs: `docker-compose logs api`
- Ensure database is healthy: `docker-compose ps`
- Verify migrations: `docker-compose exec api alembic current`

#### 2. Database Connection Issues
**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
- Wait for database health check: `docker-compose ps`
- Check database logs: `docker-compose logs db`
- Verify port mapping: Database should be accessible on port 5481

#### 3. CORS Issues
**Problem**: Frontend can't connect to backend API.

**Solutions**:
- Verify CORS_ORIGIN in environment matches frontend URL
- Check if both services are running on correct ports
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## 📊 Service Status

### Check Service Health
```bash
# All services status
docker-compose ps

# API health check
curl http://localhost:8000/health

# Database connection
docker-compose exec db psql -U postgres -d enrico_cerrini_dev -c "SELECT version();"
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs api
docker-compose logs db

# Follow logs
docker-compose logs -f api
```

## 🗄️ Database Management

### Migrations
```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Check current revision
docker-compose exec api alembic current

# Migration history
docker-compose exec api alembic history
```

### Database Access
```bash
# Connect to database
docker-compose exec db psql -U postgres -d enrico_cerrini_dev

# Reset database (⚠️ This will delete all data!)
docker-compose down -v
docker-compose up --build
```

## 🐛 Debugging

### Backend Debugging
```bash
# Enter container shell
docker-compose exec api bash

# Run Python shell with app context
docker-compose exec api python -c "from app.main import app; print('App loaded')"

# Test database connection
docker-compose exec api python -c "from app.database import engine; print(engine.url)"
```

### Frontend Debugging
```bash
# Enter frontend container (if using full stack)
docker-compose -f docker-compose.full.yml exec frontend sh

# View frontend logs
docker-compose -f docker-compose.full.yml logs frontend
```

## 📝 Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5481/enrico_cerrini_dev
JWT_SECRET=your-secure-jwt-secret
CORS_ORIGIN=http://localhost:3001
DEBUG=True
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🚢 Deployment

### Production Build
```bash
# Build production images
docker build -t enrico-backend .
docker build -t enrico-frontend ../enrico-cerrini/

# Run production
docker run -p 8000:8000 enrico-backend
docker run -p 3000:3000 enrico-frontend
```

## 📋 Development Checklist

### Before Starting Development
- [ ] Docker is running
- [ ] Environment files are configured
- [ ] Database port 5481 is available
- [ ] Ports 3000 and 8000 are available

### After Code Changes
- [ ] Run tests: `docker-compose exec api pytest`
- [ ] Check linting: `docker-compose exec api flake8`
- [ ] Format code: `docker-compose exec api black .`
- [ ] Update migrations if models changed

### Before Committing
- [ ] All tests pass
- [ ] Code is formatted
- [ ] Environment files are not committed
- [ ] Documentation is updated

## 🆘 Getting Help

1. **Check logs first**: `docker-compose logs api`
2. **Verify service health**: `docker-compose ps`
3. **Test API endpoints**: Visit http://localhost:8000/docs
4. **Database issues**: Check `docker-compose logs db`
5. **Frontend issues**: Check browser console and network tab
