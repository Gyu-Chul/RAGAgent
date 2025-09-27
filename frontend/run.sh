#!/bin/bash

echo "Starting RAGIT Frontend..."
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""
echo "Starting the application..."
echo "Open your browser and navigate to: http://localhost:8080"
echo ""
echo "Demo Accounts:"
echo "Admin: admin@ragagent.com / admin123"
echo "User:  user@ragagent.com / user123"
echo ""
python main.py