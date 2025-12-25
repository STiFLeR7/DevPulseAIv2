# Build
docker build -t devpulse-v2 .

# Run (with .env passed)
# Requires .env file to exist
docker run -p 8080:8080 --env-file .env devpulse-v2
