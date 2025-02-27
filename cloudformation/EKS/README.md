# AWS EKS Cluster with Bastion Host

해당 YAML은 CloudFormation을 이용한 테스트 인프라를 생성합니다.
매우 간단한 아키텍쳐로 구성되어 있으며, 사용자가 바로 EKS Cluster를 사용할 수 있도록 최대한의 자동화 하였습니다.


이 CloudFormation 템플릿은 다음을 포함합니다:
- **VPC** 생성 (CIDR `100.10.0.0/16`)
- 퍼블릭 / 프라이빗 / DB 서브넷 생성 및 라우팅 테이블 설정
- 인터넷 게이트웨이(IGW) 및 NAT 게이트웨이 생성
- EKS 클러스터 및 노드 그룹 생성
- 배스천 호스트(Bastion Host) 인스턴스 생성
- IAM 사용자 액세스 키를 SSM Parameter Store에 저장
- EKS Load Balancer Controller용 IAM Policy, Role 등의 구성

아래 내용을 통해 템플릿 구조와 구성 요소를 간단히 살펴볼 수 있습니다.

---

## 주요 리소스

1. **VPC 및 서브넷**
   - `YZEKSVPC`: CIDR `100.10.0.0/16` 으로 VPC를 생성합니다.
   - `PublicSubnet01`, `PublicSubnet02`: 퍼블릭 서브넷 (AZ `ap-northeast-2a`, `ap-northeast-2c`)
   - `PrivateSubnet01`, `PrivateSubnet02`: 프라이빗 서브넷
   - `DBSubnet01`, `DBSubnet02`: DB 전용 서브넷
   - `YZDBSubnetGroup01`: RDS DB Subnet Group

2. **라우팅 및 게이트웨이**
   - `InternetGateway01`, `InternetGatewayAttachment`: VPC와 IGW를 연결합니다.
   - `PublicRouteTable01`: 퍼블릭 서브넷에 IGW를 통해 0.0.0.0/0 경로를 설정합니다.
   - `NatGateway01`, `NATGatewayEIP01`: 퍼블릭 서브넷에 NAT 게이트웨이를 생성합니다.
   - `PrivateRouteTable01`: 프라이빗 및 DB 서브넷에서 NAT 게이트웨이를 통한 0.0.0.0/0 경로를 설정합니다.

3. **EC2 인스턴스 (Bastion Host)**
   - `BastionHost`: t3.micro 타입 인스턴스를 생성합니다.
   - `BastionSecurityGroup`: 배스천 호스트용 SG (아웃바운드 제한 없음)
   - `IAMRoleForEC2SSM` & `InstanceSSMProfile`: EC2가 SSM 세션 매니저를 사용할 수 있도록 하는 IAM Role/Instance Profile

4. **IAM 관련**
   - `IAMUserName` (Parameter): 클라우드포메이션 실행 시 사용할 IAM 사용자 이름
   - `YZAccessKey`, `YZSecretKeyParameter`, `YZIamUserParameter`: 
     - CF를 실행한 IAM 유저의 AccessKey, SecretKey를 SSM Parameter Store에 저장
   - `YZEmptyGroup`: CloudFormation에서 사용할 Managed Policy를 연결할 빈 그룹
   - `YZLBControllerPolicy`: AWS Load Balancer Controller를 위한 IAM Policy
   - `YZeksclusterrole`: EKS 클러스터용 Role (AmazonEKSClusterPolicy)
   - `YZeksnodegrouprole`: EKS 노드 그룹용 Role (AmazonEKSWorkerNodePolicy 등)

5. **EKS 구성**
   - `YZEKSCluster`: EKS 클러스터 생성
   - `YZEKSNodeGroup`: EKS 노드 그룹 생성 (t3.medium, Min=1, Max=2)

6. **UserData 설정**
   - Bastion Host 부팅 시 필요한 툴(kubectl, eksctl, helm) 자동 설치
   - SSM Parameter Store에서 AccessKey, SecretKey를 읽어와 AWS CLI 구성
   - `eksctl create iamserviceaccount` 명령을 통해 AWS Load Balancer Controller용 ServiceAccount 생성
   - Helm으로 AWS Load Balancer Controller 설치

---

## 파라미터(Parameters)

- **LatestAmiId**  
  SSM Parameter Store에서 AWS Linux 2 AMI를 조회하기 위한 기본값으로 설정되어 있습니다.  
  기본값: `/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2`

- **IAMUserName**  
  이 템플릿을 실행하는 IAM 사용자 이름을 입력합니다.  
  예: `myCloudFormationUser`

---

## 배포 방법

아래 예시는 AWS CLI를 통해 배포하는 방법입니다. 스택 이름, IAMUserName, 필요하다면 Region 등을 원하는 값으로 수정하세요.

```bash
aws cloudformation deploy \
  --template-file <template-file-path>.yaml \
  --stack-name MyEKSStack \
  --parameter-overrides IAMUserName=<YourIAMUser> \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region ap-northeast-2

참고
   •	--capabilities 옵션에 CAPABILITY_IAM과 CAPABILITY_NAMED_IAM이 필요합니다.
•	서브넷 CIDR, 네이밍, 리소스 크기 등을 변경하고자 하는 경우 템플릿 YAML 내 Properties 값을 수정하면 됩니다.

구성 확인
	1.	스택 생성 후
	•	VPC, Subnet, NAT Gateway 등 네트워킹 구성이 정상적으로 생성되었는지 확인하세요.
	•	EKS 클러스터와 노드 그룹 상태가 ACTIVE 인지 확인하세요.
	2.	Bastion Host 접속
	•	SSM Session Manager로 접속 가능하도록 설정되어 있으므로, AWS 콘솔 > Systems Manager > Session Manager에서 인스턴스를 찾고 접속할 수 있습니다.
	•	배스천 호스트에서 kubectl get nodes 등을 통해 노드 상태를 확인하거나, Helm 차트를 배포할 수 있습니다.
	3.	IAM Resource
	•	CloudFormation을 실행한 사용자에 대한 AccessKey, SecretKey가 SSM Parameter Store에 정상적으로 저장되었는지 확인합니다.
	•	EKS Load Balancer Controller IAM Policy(YZLBControllerPolicy)가 추가되어 있으며, ServiceAccount가 정상적으로 생성되었는지 확인하세요.

주의 사항
	•	실제 운영 환경에 배포하기 전 테스트 환경에서 검증을 권장합니다.