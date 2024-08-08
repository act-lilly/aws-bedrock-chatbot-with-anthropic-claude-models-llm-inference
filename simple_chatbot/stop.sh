#!/bin/bash
pgrep -f "streamlit run --server.enableCORS true --server.enableXsrfProtection true --server.address 0.0.0.0 --server.port 8080 main.py" | xargs kill