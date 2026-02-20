"""
Magubal Research Platform - Entry Point
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("🎯 Magubal Research Platform")
    print("   마구티어 플라이휠 기반 Stock Research")
    print("=" * 60)
    print("📡 Server: http://localhost:5000")
    print("📊 API Docs: http://localhost:5000/api/health")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
