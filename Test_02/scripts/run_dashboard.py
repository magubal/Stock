#!/usr/bin/env python3
"""
React 대시보드 테스트 실행 스크립트
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def check_node_npm():
    """Node.js와 npm 설치 확인"""
    try:
        node_version = subprocess.run(['node', '--version'], capture_output=True, text=True)
        npm_version = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        print(f"Node.js: {node_version.stdout.strip()}")
        print(f"npm: {npm_version.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Node.js 또는 npm이 설치되지 않았습니다.")
        print("https://nodejs.org/ 에서 설치해주세요.")
        return False

def install_dependencies():
    """React 프로젝트 의존성 설치"""
    frontend_path = Path(__file__).parent.parent / 'frontend'
    
    if not frontend_path.exists():
        print(f"❌ 프론트엔드 폴더를 찾을 수 없습니다: {frontend_path}")
        return False
    
    try:
        print("📦 React 의존성 설치 중...")
        result = subprocess.run(
            ['npm', 'install'],
            cwd=frontend_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("의존성 설치 완료")
            return True
        else:
            print(f"의존성 설치 실패: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 의존성 설치 중 오류: {e}")
        return False

def start_react_dev():
    """React 개발 서버 시작"""
    frontend_path = Path(__file__).parent.parent / 'frontend'
    
    try:
        print("React 개발 서버 시작 중...")
        process = subprocess.Popen(
            ['npm', 'start'],
            cwd=frontend_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("서버 시작 대기 중...")
        time.sleep(5)
        
        if process.poll() is None:
            print("React 개발 서버가 성공적으로 시작되었습니다!")
            print("브라우저에서 http://localhost:3000 을 열어보세요")
            
            # 브라우저 자동 열기
            try:
                webbrowser.open('http://localhost:3000')
                print("브라우저에서 대시보드를 열었습니다.")
            except:
                print("브라우저 자동 열기 실패. 수동으로 http://localhost:3000 을 열어주세요.")
            
            return process
        else:
            print("서버 시작 실패")
            stderr_output = process.stderr.read() if process.stderr else ""
            print(stderr_output)
            return None
            
    except Exception as e:
        print(f"❌ 서버 시작 중 오류: {e}")
        return None

def start_fastapi_backend():
    """FastAPI 백엔드 시작"""
    backend_path = Path(__file__).parent.parent / 'backend'
    
    try:
        print("🔧 FastAPI 백엔드 시작 중...")
        
        # 가상환경 확인
        venv_path = backend_path / 'venv'
        if not venv_path.exists():
            print("⚠️ 백엔드 가상환경이 없습니다. 먼저 설치해주세요:")
            print(f"cd {backend_path}")
            print("python -m venv venv")
            print("source venv/bin/activate  # Windows: venv\\Scripts\\activate")
            print("pip install -r requirements.txt")
            return None
        
        # 서버 시작
        if os.name == 'nt':  # Windows
            python_exe = venv_path / 'Scripts' / 'python.exe'
            activate_script = venv_path / 'Scripts' / 'activate.bat'
        else:  # Unix/Mac
            python_exe = venv_path / 'bin' / 'python'
            activate_script = venv_path / 'bin' / 'activate'
        
        if not python_exe.exists():
            print(f"Python 실행 파일을 찾을 수 없습니다: {python_exe}")
            return None
        
        # 환경변수 설정하여 서버 시작
        env = os.environ.copy()
        if os.name != 'nt':
            env['PATH'] = f"{venv_path}/bin:{env['PATH']}"
        
        process = subprocess.Popen(
            [str(python_exe), '-m', 'uvicorn', 'app.main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'],
            cwd=backend_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("백엔드 서버 시작 대기 중...")
        time.sleep(3)
        
        if process.poll() is None:
            print("FastAPI 백엔드가 성공적으로 시작되었습니다!")
            print("API: http://localhost:8000")
            print("API 문서: http://localhost:8000/docs")
            return process
        else:
            print("백엔드 시작 실패")
            stderr_output = process.stderr.read() if process.stderr else ""
            print(stderr_output)
            return None
            
    except Exception as e:
        print(f"❌ 백엔드 시작 중 오류: {e}")
        return None

def main():
    """메인 실행 함수"""
    print("Stock Research ONE - 대시보드 실행")
    print("=" * 50)
    
    # Node.js 확인
    if not check_node_npm():
        return
    
    # 의존성 설치
    if not install_dependencies():
        return
    
    # 백엔드 시작
    backend_process = start_fastapi_backend()
    
    # 프론트엔드 시작
    frontend_process = start_react_dev()
    
    if frontend_process and backend_process:
        print("\n모든 서비스가 실행 중입니다!")
        print("종료하려면 Ctrl+C를 누르세요.")
        
        try:
            # 프로세스가 종료될 때까지 대기
            frontend_process.wait()
        except KeyboardInterrupt:
            print("\n서비스 종료 중...")
            frontend_process.terminate()
            if backend_process:
                backend_process.terminate()
    else:
        print("서비스 시작 실패")

if __name__ == "__main__":
    main()