# mediavault-manager

## Docker Instructions

### Building and Running with Docker

1. Build the Docker image:
```bash
docker build -t mediavault-manager .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 --name mediavault mediavault-manager
```

3. Test the health endpoint:
```bash
curl http://localhost:8000/system/health
```

### Container Management

To stop the container:
```bash
docker stop mediavault
```

To remove the container:
```bash
docker rm mediavault
```

The application will be available at `http://localhost:8000` when running.
