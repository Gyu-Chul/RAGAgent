1. 사용된 프레임워크 : X
2. 파이썬 최소 3.8 이상
3. python main.py 실행


자바 스크립트 파싱 로직을 사용하기 위해서는 해당 모듈 필요.
npm install acorn (js 파싱하기 위해 필요)





자바 파싱 로직을 사용하기 위해서는 JDK,maven 설치 필요.

윈도우 환경에서는 Chocolatey 를 통해서 간편 설치 가능


1. Chocolatey 설치 : ``` Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))```
2. maven 설치 : ```choco install maven```

자바는 microsoft open jdk 17.0.11 를 이용해 설치.