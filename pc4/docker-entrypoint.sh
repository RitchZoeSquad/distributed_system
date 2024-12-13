#!/bin/bash

if [ "$SERVICE_TYPE" = "leak_check" ]; then
    echo "Starting Leak Check Worker..."
    python src/main_leak_check.py
else
    echo "Starting Domain Email Worker..."
    python src/main.py
fi 