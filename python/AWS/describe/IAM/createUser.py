import boto3
import time as t
import pyotp
import datetime
import os
import subprocess

### Last updated : 2022-11-29
### Created by Youngjin Park 

### 서비스 설정
###############
service = input("Profile name을 입력하세요:")
session = boto3.Session(profile_name=service)
client_iam = session.client('iam')
client_sts = session.client('sts')
iam = session.resource('iam')
accountID = client_sts.get_caller_identity()["Account"]

### 권한만 추가

### 유저 정보 기입
###############
userName = input("사용자 이름을 입력하세요: ")
userPassword = input("사용자의 패스워드를 입력하세요(8자 이상, 대문자, 특수문자 포함): ")

### Group 기입
###############
while True:
    groupAdd = input("그룹에 유저를 추가하겠습니까?(y/n)")
    groupAdd.isalpha() == False
    if groupAdd.isalpha() == True:
        gruopAdd = groupAdd.lower()
        break
    print("y/n 중 하나를 입력하세요.")

if groupAdd == "y":
    print('=================')
    print('=== 그룹 목록 ===')
    print('=================')
    os.system('aws iam list-groups --query \'Groups[*].GroupName\' --profile '+ service)
    groupName = input('유저가 속할 그룹을 선택해주세요:')

### Policy 기입
##############
while True:
    policyAdd = input("유저에 권한을 추가하겠습니까?(y/n)")
    policyAdd.isalpha() == False
    if policyAdd.isalpha() == True:
        policyAdd = policyAdd.lower()
        break
    print("y/n 중 하나를 입력하세요.")

policyName = "temp"
policyList = []
policyListarn = []
i = 0

if policyAdd == "y":
    print('=============================================')
    print('========= Policy Name을 정확히 입력해 주세요. ')
    print('=============================================')
    while policyName != "":
        policyName = input("권한 이름을 입력해주세요(종료시 공백 엔터)")
        policyList.insert(i,policyName)
        i += 1
i -= 1

for j in range (i):
    policyArn = subprocess.check_output('aws iam list-policies --query \'Policies[?PolicyName==`' + policyList[j] +'`].{ARN:Arn}\' --output text --profile ' + service, shell = True,universal_newlines=True)
    policyListarn.insert(j,policyArn[:-1])

### 유저 생성
################
response_create_user = client_iam.create_user(
            UserName = userName
            )
print('사용자 ' + userName + ' 생성완료')
t.sleep(2)

### MFA 생성
#################
response_mfa = client_iam.create_virtual_mfa_device(
            VirtualMFADeviceName = userName
                )

string_seed = response_mfa['VirtualMFADevice']['Base32StringSeed']
qrbytes = response_mfa['VirtualMFADevice']['QRCodePNG']

with open(userName + '(' + service +')' + '.png', mode='wb' ) as f:
        f.write(qrbytes)
        f.close()

totp = pyotp.TOTP(string_seed)
# the code from 30 seconds ago
code_1 = totp.generate_otp(totp.timecode(datetime.datetime.now() - datetime.timedelta(seconds=30)))
# the current code
code_2 = totp.generate_otp(totp.timecode(datetime.datetime.now()))

response_create_mfa = client_iam.enable_mfa_device(
    UserName=userName,
    SerialNumber='arn:aws:iam::' + accountID + ':mfa/' + userName,
    AuthenticationCode1=code_1,
    AuthenticationCode2=code_2
)

print ('사용자 ' + userName + ' MFA 등록완료')
t.sleep(2)

### 패스워드 생성
#################

response_create_password = client_iam.create_login_profile(
    UserName = userName,
    Password = userPassword,
    PasswordResetRequired = True
)
print ('사용자 ' + userName + ' 패스워드 등록완료')
t.sleep(1)

### 그룹에 유저 추가
################
if groupAdd == "y":
    user = iam.User(userName)

    response_add_group = user.add_group(
        GroupName = groupName
    )
    print ( '그룹 ' + groupName + '에 사용자' + userName + " 추가완료")

### 유저에 권한 추가
###############
if policyAdd == "y":
    user = iam.User(userName)

    for k in range (i):
        response_attach_policy = user.attach_policy(
            PolicyArn = policyListarn[k]
            )
        print ('사용자 ' + userName + '에 ' + policyList[k] +' 권한 추가 완료')
        t.sleep(0.5)