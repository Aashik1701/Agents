# 🌐 MongoDB Atlas Setup Guide

## Step 1: Update Configuration

Edit `config.py` and replace the placeholder values:

```python
# Replace these with your actual Atlas credentials
MONGODB_USERNAME = "your_actual_username"
MONGODB_PASSWORD = "your_actual_password"
```

## Step 2: Test Atlas Connection

```bash
# Activate virtual environment
source venv/bin/activate

# Test the connection
python test_atlas.py
```

## Step 3: Add Initial Data (Optional)

### Option A: Add minimal starter data
When running `test_atlas.py`, choose 'y' to add starter data.

### Option B: Use the management script
```bash
python manage_faqs.py
```

### Option C: Import from JSON
```bash
# Use the sample file or create your own
python manage_faqs.py
# Choose option 4 and enter: sample_faqs.json
```

### Option D: Use the web API
```bash
curl -X POST http://localhost:5000/add_faq \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "answer": "This is a test from Atlas!"}'
```

## Step 4: Run the Application

```bash
python app.py
```

## Step 5: Verify Real-time Connection

1. Visit: http://127.0.0.1:5000/health
2. Check: http://127.0.0.1:5000/stats
3. Test the chat interface: http://127.0.0.1:5000/

## Security Checklist

✅ **IP Whitelist**: Ensure your IP is added to Atlas network access
✅ **Database User**: Create a database user with read/write permissions
✅ **Connection String**: Verify the connection string is correct
✅ **Credentials**: Keep your username/password secure

## Troubleshooting

### Connection Issues
- Check your Atlas cluster status
- Verify IP whitelist settings
- Confirm username/password are correct

### Empty Database
- Run `python test_atlas.py` to add starter data
- Use `python manage_faqs.py` to add custom FAQs
- Import data using the `/add_faq` API endpoint

### Performance Tips
- Create text indexes for better search performance
- Monitor Atlas metrics in the dashboard
- Consider connection pooling for production

## Real-time Features

🔄 **Live Updates**: Changes to Atlas database are immediately available
📊 **Statistics**: Real-time FAQ count and database stats
➕ **Dynamic Adding**: Add new Q&A pairs without restarting the app
🔍 **Smart Search**: Enhanced search with exact, partial, and text matching
