#!/bin/bash

# Start Backend FastAPI in background on port 7860
cd backend && uvicorn api:app --host 0.0.0.0 --port 7860 &

# Start Frontend Node.js in foreground
cd frontend && node index.js
