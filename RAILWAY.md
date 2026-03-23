# Railway Configuration

To deploy successfully on Railway, you need to set the following environment variables in your project settings:

```
DATABASE_URL        # Auto-injected by Railway Postgres plugin
JWT_SECRET          # Strong random secret
JWT_REFRESH_SECRET  # Strong random secret
SECRET_KEY          # Strong random secret
CORS_ORIGIN         # Your frontend Railway URL e.g. https://yourapp.up.railway.app
ENVIRONMENT         # production
DEBUG               # False
```

Do not hardcode these variables anywhere in the codebase.
