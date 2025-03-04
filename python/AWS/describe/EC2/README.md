# AWS EC2 Information Collector

이 저장소는 CSV 파일로 저장된 AWS 자격증명을 활용하여 여러 계정의 EC2 인스턴스 정보를 수집하는 Python 스크립트를 제공합니다.  
스크립트는 각 자격증명 파일에서 AWS 세션을 생성하고, 계정 ID에 매핑된 리전별로 EC2 인스턴스 정보를 조회한 후, 결과를 Excel 파일로 저장합니다.

---

## ⚠️ 중요 경고

> **WARNING:**  
> 로컬 파일이나 저장소에 AWS 자격증명을 하드코딩하지 마세요.  
> AWS CLI나 환경 변수를 사용하여 자격증명을 안전하게 관리하시기 바랍니다.

---

## 사전 요구 사항

- Python 3.x  
- 다음 Python 라이브러리:  
  - `boto3`  
  - `pandas`  
  - `openpyxl` (Excel 파일 저장용)  
  - `glob`  
  - `logging`  
- CSV 파일 형태의 AWS 자격증명 파일  
  - CSV 파일에는 `Access key ID`와 `Secret access key` 컬럼이 존재해야 합니다.
- AWS 계정별 리전 정보를 매핑하는 `account_region_map` 변수 설정

---

## 설정 방법

1. **저장소 클론**  
   ```bash
   git clone https://github.com/<your_username>/<your_repo_name>.git
   cd <your_repo_name>

2. **필수 라이브러리 설치**
    ```bash
    pip install boto3 pandas openpyxl

3. **스크립트 설정**
•	CREDENTIALS_DIR 변수를 수정하여 자격증명 파일이 저장된 디렉토리 경로를 지정합니다.
•	account_region_map 딕셔너리를 수정하여 각 AWS 계정 ID에 해당하는 리전 목록을 설정합니다.
    ```bash
    account_region_map = {
    "123456789012": ["ap-northeast-2"],
    "987654321098": ["us-west-2", "us-east-1"]
    }
---
## 사용 방법
스크립트를 실행하여 EC2 인스턴스 정보를 수집합니다.
    
1. **코드 실행**
    ```bash
    python <script_name>.py

실행 시 스크립트는 다음과 같은 작업을 수행합니다
•	지정된 CREDENTIALS_DIR 내의 모든 CSV 파일을 읽어 AWS 자격증명을 로드합니다.
•	각 CSV 파일에 대해 AWS 세션을 생성하고, STS를 통해 계정 ID를 확인합니다.
•	계정 ID에 매핑된 리전 목록에 따라 각 리전에서 EC2 인스턴스 정보를 조회합니다.
•	인스턴스의 상세 정보(Instance ID, 인스턴스 타입, 상태, Public/Private IP, AutoScaling Group, Launch Template 등)를 수집합니다.
•	수집된 데이터를 hosts_ec2_YYYY-MM-DD-HH-MM.csv 형식의 Excel 파일로 저장합니다.