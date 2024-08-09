#!/bin/bash
python -m streamlit run --server.enableCORS true --server.enableXsrfProtection true --server.address 0.0.0.0 --server.port 8080 main.py & echo "Service started with process ID: $!"