# MongoDB Atlas Configuration
# Replace these with your actual credentials
MONGODB_USERNAME = "Cluster20526"  # ← Replace with your Atlas username
MONGODB_PASSWORD = "aashik1701"  # ← Replace with your Atlas password
MONGODB_CLUSTER = "cluster20526.g4udhpz.mongodb.net"
MONGODB_DATABASE = "chatbotDB"

# Full Atlas URI
MONGODB_URI = f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_CLUSTER}/?retryWrites=true&w=majority&appName=Cluster20526"

# For local development (fallback)
LOCAL_MONGODB_URI = "mongodb://localhost:27017/"

# Choose connection type
USE_ATLAS = False  # Set to True when Atlas credentials are fixed
