#!/usr/bin/env python3
"""
Lightweight startup script that avoids loading heavy ML models during development
"""

import os
import sys

# Set environment variables to reduce TensorFlow verbosity and memory usage
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logs
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN optimizations
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU usage (faster startup)

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main application entry point"""
    print("🚀 Starting Remote Work Monitor (Lightweight Mode)")
    print("=" * 50)
    
    try:
        from app import create_app
        
        # Create Flask app
        app = create_app()
        
        print("✅ Application initialized successfully")
        print("🌐 Server starting on http://localhost:5000")
        print("📝 Note: Face recognition models load on first use")
        print("⚡ Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Run the application
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=False,  # Disable reloader to prevent double loading
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()