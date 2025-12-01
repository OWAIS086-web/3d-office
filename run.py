#!/usr/bin/env python3
"""
Run script for Remote Work Monitor
This script starts the application with proper configuration
"""

import os
import sys
from app import create_app

def main():
    """Main function to run the application"""
    print("Starting Remote Work Monitor...")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    # Get configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"Server starting on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print("\nAccess the application at:")
    print(f"  http://localhost:{port}")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run the application
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        print("Goodbye!")
    except Exception as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
