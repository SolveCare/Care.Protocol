**케어.프로토콜(Care.Protocol) 사양**

케어.프로토콜(Care.Protocol)은 케어.네트워크(Care.Network)를 구성하는 개체의 롤, 관계, 케어.저니, 케어.카드, 케어.이벤트 등의 동작을 정의한다. 

케어.프로토콜을 통해 모든 사용자는 분산형 애플리케이션(케어.카드 등)으로 구성된 개인형, 자율형, 토큰형 및 불변성의 완전한 분산형 디지털 네트워크를 작성할 수 있다

또한 케어.프로토콜을 통해 모든 사용자가 솔브케어 플렛폼을 저렴한 비용으로 관리할 수 있다.

케어 프로토콜은 네트워크에 대한 규칙을 지정할 뿐만 아니라 네트워크 구성요소에 대해 해당 규칙을 적용하여 사전 정의된 동작을 준수하는지 확인한다. 

케어 프로토콜의 모든 버전은 블록체인으로 게시되어 변형할 수 없으며, 추적이 가능하고 네트워크로 쉽게 배포할 수 있다.

케어 프로토콜은 구성요소 간 통신에 대한 규칙이나 비즈니스 계약을 일련으로 정의하고 전체 네트워크를 통제한다.


- **케어 네트워크 메타데이터** 

이 섹션에서는 네트워크 이름 및 관리 버전과 같은 전체 네트워크 정보에 대해 설명한다.  네트워크 작성자는 상위 수준의 네트워크 메타데이터를 정의할 수 있다.



|필드 이름|값 유형|설명|
| :- | :- | :- |
|name|문자열|<p>1. 케어 네트워크의 이름.</p><p>2. 필수</p>|
|description|문자열|<p>1. 네트워크에 대한 설명.</p><p>2. 필수</p>|
|version|숫자|<p>1. 케어 네트워크의 버전. </p><p>참고: 본 버전은 네트워크 메타데이터 값이 변경함에 따라 업데이트된다.</p><p>1. 필수</p>|
|certificates|문자열|<p>1. 제삼자 유효성 검사 및 인증 레퍼런스 번호. </p><p>2. 필수</p>|
|publish\_date|문자열|<p>1. 네트워크 프로토콜의 발행일. </p><p>2. 필수</p>|
|effective\_date|문자열|<p>1. 케어 네트워크에 적용되는 본 프로토콜의 발효일.  </p><p>2. 필수</p>|
|protocol\_version|숫자|<p>1. 네트워크 프로토콜의 버전. </p><p>참고: 본 버전은 네트워크 프로토콜이 변경함에 따라 업데이트된다.</p><p>3. 필수</p>|

```json
{
    "name": "CAN",
    "description": "Care Administration Network",
    "version": 1.0,
    "certificates": "CERT-001",
    "publish_date": "25-03-2021",
    "effective_date": "01-04-201",
    "protocol_version_number": "1.0"
}
```

- **케어 네트워크 설정 (네트워크 설정 (SOLVE\_settings))**

이번 섹션은 케어.프로토콜 네트워크 및 네트워크 이벤트에 대한 SOlVE(솔브케어 가상화폐)에 대한 설정이다. 솔브케어 토큰은 케어.포로토콜의 이벤트 수준에서 구성할 수 있다. 


|필드 이름|값 유형|설명|
| :- | :- | :- |
|solve\_token\_usage|JSON 값|<p>1. 네트워크 내 솔브 토큰(SOLVE Token)의 사용량. </p><p>2. 필수</p>|
|deposit\_value|문자열|<p>1. 솔브 토큰의 예치 값.</p><p>2. 필수</p>|
|redemption\_value|문자열|<p>1. 환매 값. </p><p>2. 필수</p>|
|solve\_gas\_setting|JSON 값|<p>1. 솔브 가스(SOLVE Gas) 사용량의 설정. </p><p>2. 필수</p>|
|event\_wise\_cost|배열|<p>2. 솔브 토큰 (SOLVE Token)의 이벤트성 비용. </p><p>3. 필수</p>|
|event|문자열|<p>1. 네트워크 상 거래에 이용된 이벤트. </p><p>2. 필수</p>|
|cost|롱 (Long) 데이터|<p>1. 각 이벤트 거래 당 솔브 가스 (SOLVE Gas)의 비용.  </p><p>3. 필수</p>|

```json
{
  "network_settings": {
      "solve_token_usage": {
        "deposit_value": "Market",
        "redemption_value": "Deposit",
        "solve_gas_setting": {
          "event_wise_cost": [
            {
              "event": "04001",
              "cost": 10
            },
            {
              "event": "04002",
              "cost": 20
            },
            {
              "event": "04003",
              "cost": 10
            },
            {
              "event": "04004",
              "cost": 20
            },
            {
              "event": "04005",
              "cost": 21
            },
            {
              "event": "04006",
              "cost": 10.5
            }
          ]
        }
      }
    }
}
```

- **네트워크 참가자 (역할)**: 케어 네트워크 참가자 및 계약 (역할 및 관계)

이번 섹션은 케어.프로토콜의 역할(role)을 정의 한다. 케어.네트워크(Care Network) 분산형 플랫폼에서 이벤트를 생성하거나 사용하는 사용자 역할로 설정으로 사용자 역할은 의사, 환자, 관리 조정자, 보험 제공자, 고용주 등과 같은 역할을 정할 수 있다. 

|필드 이름|값 유형|설명|
| :- | :- | :- |
|id|숫자|<p>1. 네트워크 전반에서 고유한 역할 아이디. </p><p>2. 자동생성</p><p>3. 필수</p>|
|name|문자열|<p>1. 네트워크 참여자 (역할)의 이름</p><p>2. 필수</p>|
|description|문자열|<p>1. 네트워크 참여자 (역할)에 대한 설명</p><p>2. 필수</p>|
|type|문자열|<p>1. 역할의 유형 </p><p>&emsp;a. 역할 (케어 지갑 (Care Wallet) 역할)</p><p>&emsp;b. 통합 역할 (플랫폼 역할)</p><p>2. 필수</p>|
|status|문자열|<p>1. 역할의 상태 </p><p>&emsp;a. 활성화</p><p>&emsp;b. 비활성화</p><p>2. 필수</p>|
|version|숫자|<p>1. 역할의 버전. </p><p>참고: 본 버전은 역할 메타데이터 값이 변경함에 따라 업데이트된다.</p><p>2. 필수</p>|
|network|문자열|<p>1. 케어 관리 네트워크 (Care Administration Network)의 이름.  </p><p>2. 필수</p>|

```json
{
  "roles": [
          {
            "id": "01001",
            "name": "Patient",
            "description": "Patient role for the CAN",
            "type": "Wallet",
            "status": "Active",
            "version": 1.0,
            "network": "CAN",
            "allow_events_with_role": [
              "01002"
            ]
          },
          {
            "id": "01002",
            "name": "Doctor",
            "description": "Patient role for the CAN",
            "type": "Wallet",
            "status": "Active",
            "version": 1.0,
            "network": "CAN",
            "allow_events_with_role": [
              "01001"
            ]
          }
      ]
}
```

- **경로(저니):** 케어 네트워크 참가자의 기능 및 비즈니스 흐름 (케어 경로 (Care Journeys)) 

케어.저니(Care.Journey)는 케어.카드(Care.Card)에 컬렉션으로 순서와 동작을 연결한다. 사용자가 플랫폼에서 작업을 수행하고 이벤트를 생성하기 위해 한 화면에서 다른 화면으로 상호 작용하는 것으로 예를 들어 의료 예약 등과 같은 이벤트를 플렛폼에서 설정할 수 있다. 

|필드 이름|값 유형|설명|
| :- | :- | :- |
|id|숫자|<p>1. 네트워크 전반에서 고유한 경로 아이디. </p><p>2. 자동생성</p><p>3. 필수</p>|
|name|문자열|<p>1. 경로의 이름 (케어 경로 (Care Journey))</p><p>2. 필수</p>|
|description|문자열|<p>1. 경로에 대한 설명 (케어 경로)</p><p>2. 필수</p>|
|status|문자열|<p>1. 경로의 상태</p><p>&emsp;a. 활성화</p><p>&emsp;b. 비활성화</p><p>2. 필수</p>|
|version|숫자|<p>1. 경로의 버전. </p><p>참고: 본 버전은 경로 메타데이터 값이 변경함에 따라 업데이트된다.</p><p>2. 필수</p>|
|start\_card\_ref\_id|숫자|<p>1. 경로 시작 시 사용 카드.</p><p>2. 선택</p>|
|roles|배열|<p>1. 본 경로와 관련된 역할 목록. </p><p>2. 필수</p>|
|integration\_roles|배열|<p>3. 본 경로와 관련된 통합 역할 (서비스) 목록. </p><p>4. 필수 / 선택</p>|

```json
{
  "journeys": [
      {
        "id": "02001",
        "name": "Appointment",
        "description": "Appointment Journey",
        "status": "Active",
        "version": 1.0,
        "start_card_ref_id": "03101",
        "roles": [
          "01001",
          "01002"
        ]
      },
      {
        "id": "02003",
        "name": "Find Doctor",
        "description": "Find a doctor Journey for patient",
        "status": "Active",
        "version": 1.0,
        "start_card_ref_id": "03201",
        "roles": [
          "01001",
          "01002"
        ]
      }
    ]
}
```

- **케어.카드(Card)**: 참가자의 기능을 위한 동적 사용자 인터페이스 정의 (케어 카드 (Care Cards))

케어.카드는 케어.월렛(CareWallet) 및 솔브케어 플렛폼의 기본 정보 블록으로 간주할 수 있는 캡슐화된 개체 모델이다. 데이터 수집 또는 표와 마찬가지로 카드는 다양한 데이터 유형과 실행 기능을 캡슐화하는 개체이다. 카드는 월렛 및 노드(Node)에서 소유할 수 있으며, 여러 데이터 유형, 권한 속성, 암호화 및 인터페이스가 이벤트에 연결된 구조이다. 

케어.월렛은 기본 데이터 및 동작 캡슐화가 포함된 사용자 인터페이스 카드라고 볼 수 있다. 

이번 섹션은 케어.프로토콜에서 케어.카드와 케어,저니를 구축하는 내용이다. 


|필드 이름|값 유형|설명|
| :- | :- | :- |
|id|숫자|<p>1. 네트워크 전반에서 고유한 카드 아이디. </p><p>2. 자동생성</p><p>3. 필수</p>|
|name|문자열|<p>1. 카드의 이름 (케어 카드 (Care Card))</p><p>2. 필수</p>|
|description|문자열|<p>2.카드에 대한 설명 (케어 카드) </p><p>3. 필수</p>|
|status|문자열|<p>1. 카드의 상태 </p><p>&emsp;a. 활성화</p><p>&emsp;b. 비활성화</p><p>2. 필수</p>|
|version|숫자|<p>1. 카드의 버전. </p><p>참고: 본 버전은 카드 메타데이터 값이 변경함에 따라 업데이트된다.</p><p>2. 필수</p>|
|role|문자열|<p>1. 카드에 속하는 네트워크 참가자 (역할).</p><p>2. 필수</p>|
|journey|문자열|<p>1. 카드에 속하는 여정. </p><p>2. 필수</p>|
|card\_definition\_ref|문자열|<p>1. UI 구성요소 정의에 대한 참조. (별도 정의 JSON 파일) 본 정의는 동적 카드 구성으로 이루어져 있다. </p><p>&emsp;a. 카드 데이터</p><p>&emsp;b. 카드 레이아웃</p><p>&emsp;c. 카드 UI 액션</p><p>2. 필수</p><p>3. JSON 파일 – card\_definition.json</p>|
|wallet\_events|배열|<p>1. 본 카드에 대한 지갑 이벤트 목록. (지갑 내부 이벤트 및 수신 이벤트에 해당한다.)</p><p>2. 필수</p>|
|node\_events|배열|<p>1. 본 카드에 대한 노드 이벤트 목록. (기타 역할에 대한 발신 이벤트에 해당한다.)</p><p>2. 필수</p>|
|care\_tag\_id|배열|<p>1. Care.Tag레퍼런스 아이디</p><p>2. 필수</p>|

```json
{
  "cards": [
          {
            "id": "03101",
            "name": "Request_Appointment",
            "description": "Request an appointment wallet card for the Patient ",
            "status": "Active",
            "version": 1.0,
            "role": "01001",
            "journey": "02001",
            "card_definition_ref": "03101.json",
            "wallet_events": [
              "04101"
            ],
            "node_events": [
              "04102"
            ]
          },
          {
            "id": "03102",
            "name": "Complete_Appointment",
            "description": "Appointment complete wallet card for the Doctor ",
            "status": "Active",
            "version": 1.0,
            "role": "01002",
            "journey": "02001",
            "care_tags": {
              "id": "2928839",
              "allowed_networks": "global",
              "data_tags": [
                "Referred speciality",
                "Pre-authorization",
                "Urgency",
                "Reason"
              ]
            },
            "card_definition_ref": "03102.json",
            "wallet_events": [
              "04103"
            ],
            "node_events": [
              "04104"
            ]
          }
     ]
}
```

**케어.테그 (care tag):** 익명의 비동기 데이터 및 이벤트 교환을위한 토큰 기반 상호 운용성


|필드 이름|값 유형|설명|
| :- | :- | :- |
|id|숫자|<p>1. 네트워크에서 고유 한 카드 ID입니다.</p><p>2. 자동 생성</p><p>3. 필수</p>|
|allowed\_networks|배열|<p>1. care.tag의 구독자와 공유하는 데이터 태그 목록입니다</p><p>2. 필수</p>|
|data\_tags|배열|<p>1. 케어.테그(care.tag) 가입자와 공유하는 데이터 태그 목록</p><p>2. 필수</p>|
|SOLVE\_fee|숫자|<p>1. 기본적으로 0, 재정의 가능</p><p>2. 필수</p>|

```json
{
  "care_tags": {
      "id": "2928839",
      "allowed_networks": "global",
      "data_tags": [
        "Referred speciality",
        "Pre-authorization",
        "Urgency",
        "Reason"
      ]
  }
},
```

- **이벤트**: 케어 네트워크 참여자와 메시지 및 이벤트 구조 간의 의사소통. (이벤트)

솔브케어 분산형 플랫폼은 노드에서 데이터를 유지하고, 이벤트를 기반으로 데이터를 계산하여 사용할 수 있도록 한다. 플랫폼은 이벤트 처리 중심으로 구축된다. 각 이벤트는 이벤트 타임라인에 대한 완전한 감사 기능을 통해 블록체인에 고정되어 있다. 케어.프로토콜 이벤트는 네트워크 참가자 역할이 이벤트를 생성하거나 소비하므로 구성하는데 가장 중요한 구성 요소이다. 예를 들어 의사가 환자에게 처방전을 보내는 것이 '이벤트'이다.


모든 이벤트에는 사용자가 케어월렛 혹은 노드에서 케어.카드를 통해 이뤄진다. 



|필드 이름|값 유형|설명|
| :- | :- | :- |
|id|숫자|<p>1. 네트워크 전반에서 고유한 이벤트 아이디. </p><p>2. 자동생성</p><p>3. 필수</p>|
|name/code|문자열|<p>1. 이벤트의 이름</p><p>2. 필수</p>|
|description|문자열|<p>1. 이벤트에 대한 설명 </p><p>2. 필수</p>|
|type|문자열|<p>1. 이벤트의 유형</p><p>&emsp;a. 지갑 이벤트</p><p>&emsp;b. 노드 이벤트</p><p>2. 필수</p>|
|card|문자열|<p>1. 카드 레퍼런스 아이디</p><p>2. 필수</p>|
|from\_role|문자열|<p>1. 이벤트 제작자의 역할. </p><p>2. 필수 (If ‘type’ is Node event)</p>|
|to\_role|문자열|<p>3. 이벤트 수신자의 역할.</p><p>4. 필수 (If ‘type’ is Node event)</p>|
|status|문자열|<p>1. 이벤트의 상태 </p><p>&emsp;a. 활성화</p><p>&emsp;b. 비활성화</p><p>2. 필수</p>|
|version|숫자|<p>1. 이벤트의 버전. </p><p>참고: 본 버전은 이벤트 메타데이터 값이 변경함에 따라 업데이트된다. </p><p>2. 필수</p>|
|event\_definition\_ref|문자열|<p>1. 이벤트 페이로드 정의 JSON 레퍼런스. 본 정의는 이벤트 페이로드 필드 및 통제로 이루어져 있다. </p><p>2. 필수 </p><p>3. JSON 파일– event\_definition.json</p>|
|wallet\_event\_handlers|배열|<p>1. 본 이벤트를 위한 지갑 이벤트 핸들러 목록. (지갑 내부 이밴트 핸들러 및 수신 이벤트 핸들러로 구성된다.)</p><p>2. 필수 (If ‘type’ is wallet event)</p>|
|<p>node\_event\_handlers </p><p></p>|배열|<p>1. 본 이벤트를 위한 노드 이벤트 핸들러 목록. (발신 이벤트에 대한 핸들러에 해당한다. – 노드 이벤트</p><p>2. 필수 (‘유형’이 노드 이벤트인 경우)</p>|
|next\_event|문자열|<p>1. 다음 이벤트</p><p>2. 필수</p>|
|exclusive\_consent\_needed|숫자|<p>4. 네트워크 전반에서 고유한 이벤트 아이디. </p><p>5. 자동생성</p><p>1. 필수</p>|

` `참고: 

1. 노드 이벤트
   1. 노드 이벤트 핸들러
1. 지갑 이벤트
   1. 지갑 이벤트 핸들러

```json
{
  "events": [
      {
        "id": "04101",
        "name": "Available.Doctors",
        "code": "PT.AVAILABLE.DOCTORS",
        "description": "GET available doctors from the wallet node",
        "status": "Active",
        "version": 1.0,
        "type": "Wallet_Event",
        "card": "03101",
        "event_definition_ref": "04101.json",
        "wallet_event_handlers": [
          "05001"
        ],
        "next_event": "04102"
      },
      {
        "id": "04102",
        "name": "Appointment.Request",
        "description": "Book an appointment with Doctor",
        "code": "PT.APPOINTMENT.REQUEST",
        "status": "Active",
        "version": 1.0,
        "type": "Node_Event",
        "event_definition_ref": "04102.json",
        "distribution_type": "node_to_node",
        "from_role": "01001",
        "to_role": "01002",
        "wallet_event_handlers": [
          "05002"
        ],
        "node_event_handlers": [
          "05003"
        ],
        "next_event": "04103"
      }
    ]
}
```

- **이벤트 핸들러 (event\_handler)**: 각 케어 네트워크 참가자에 대한 이벤트 및 메시지와 관련된 일련의 비즈니스 규칙 (이벤트 핸들러)

이벤트 핸들러 섹션. 케어.프로토콜은 각 관리 네트워크 참가자(이벤트 핸들러)에 대한 이벤트/메시지 관련 비즈니스 규칙 집합을 정의한다. 이벤트 핸들러의 기능과 실제 비즈니스에 필요한 기능을 제공한다. 


|필드 이름|값 유형|설명|
| :- | :- | :- |
|id|숫자|<p>1. 네트워크 전반에서 고유한 이벤트 핸들러 아이디.</p><p>2. 자동생성</p><p>3. 필수</p>|
|Name|문자열|<p>1. 이벤트 핸들러의 이름</p><p>2. 필수</p>|
|description|문자열|<p>1. 이벤트 핸들러에 대한 설명</p><p>2. 필수</p>|
|type|문자열|<p>1. 이벤트 핸들러의 유형</p><p>&emsp;a. 지갑 이벤트 핸들러</p><p>&emsp;b. 노드 이벤트 핸들러</p><p>2. 필수</p>|
|status|문자열|<p>1. 이벤트 핸들러의 상태 </p><p>&emsp;a. 활성화</p><p>&emsp;b. 비활성화</p><p>2. 필수</p>|
|version|숫자|<p>1. 이벤트 핸들러의 버전. </p><p>참고: 본 버전은 이벤트 핸들러의 메타데이터 값이 변경함에 따라 업데이트된다.</p><p>2. 필수.</p>|
|event|문자열|<p>1. 본 이벤트 핸들러의 이벤트. 이는 곧 이벤트 레퍼런스 넘버에 해당한다. </p><p>2. 필수.</p>|
|type|문자열|<p>1. 이벤트 핸들러의 유형. </p><p>&emsp;a. 지갑 이벤트 핸들러 (wallet\_event\_handler)</p><p>&emsp;b. 노드 이벤트 핸들러 (node\_event\_handler)</p><p>2. 필수</p>|
|event\_handler\_definition\_ref|문자열|<p>1. 이벤트 핸들러 정의에 대한 래퍼런스. (별도 정의 JSON 파일) 본 정의는 이벤트 핸들러 유형을 기반으로 하는 이벤트 핸들러 구성으로 이루어져 있다. </p><p>2. 필수</p><p>3. JSON 파일 – event\_handler\_definition.json</p>|

```json
{
  "event_handlers": [
      {
        "id": "05001",
        "name": "Available.Doctors.Event.Handler",
        "description": "Get available doctors from the wallet node",
        "status": "Active",
        "version": 1.0,
        "event": "04101",
        "type": "Wallet_Event_Handler",
        "event_handler_definition_ref": "05001.json"
      },
      {
        "id": "05002",
        "name": "Appointment.Request",
        "description": "Create an appointment event",
        "status": "Active",
        "version": 1.0,
        "event": "04102",
        "type": "Wallet_Event_Handler",
        "event_handler_definition_ref": "05001.json"
      }
    ]
}
```



- **솔브 토큰 (SOLVE Token) (solve\_tokens)**

솔브케어 토큰은 솔브의 유틸리티 토큰이다. 솔브케어 플렛폼은 관리 분산형 의료 플랫폼으로 블록체인 기술을 기반으로 구축된다. 솔브토큰은 전 세계 의료 및 혜택 지급을 위해 설계되었다. 

솔브케어 토큰은 플랫폼의 연료 역할을 하며 다양한 활용과 관련된 많은 가치를 창출하는 프로그래밍이 가능한 토큰입니다.


이번 섹션은 케어.프로토콜에서 SOLVE(솔브케어 토크) 네트워크에 대한 구성이다.


|필드 이름|값 유형|설명|
| :- | :- | :- |
|transfer\_from\_other\_network|JSON 값|<p>1. 본 구역에서는 다른 네트워크로부터 전송된 토큰에 대해 설명한다. </p><p>2. 필수</p>|
|allow|문자열|<p>1. 다른 네트워크로 전송이 허용된 토큰, </p><p>&emsp;a. 예</p><p>&emsp;b. 아니오</p><p>2. 필수</p>|
|payment\_options|배열|<p>1. 토큰 전송에 대한 지불 방법 목록.</p><p>&emsp;a. CC</p><p>&emsp;b. Paytm</p><p>&emsp;c. Transfer Wise</p><p>2. ‘허용’에서 대답이 ‘예’인 경우 필수</p>|
|transfer\_within\_network|JSON 값|<p>1. 본 구역에서는 동일한 네트워크 내에서 전송된 토큰에 대해 설명한다.</p><p>2. 필수</p>|
|allow|문자열|<p>1. 동일 네트워크 내에서 전송이 허용된 토큰, </p><p>&emsp;a. 예</p><p>&emsp;b. 아니오</p><p>1. 필수</p>|
|transfer\_mapping|배열|<p>1. 네트워크 내에서 토큰을 전송할 역할 매핑. 각 매핑에는 두 개의 값이 필요하다.</p><p>&emsp;a. 발신인 역할 (from\_role)</p><p>&emsp;b. 수신인 역할 (to\_role)</p><p>2. 필수 if ‘Allow’ is ‘YES’</p>|
|withdrawn\_tokens\_from\_network|배열|<p>1. 본 구역에서는 네트워크로부터 인출한 토큰에 대해 설명한다.</p><p>2. 필수</p>|

```json
{
  "solve_token": {
      "transfer_from_other_network": {
        "allow": "Yes",
        "payment_options": [
          "CC",
          "PayTM",
          "Transferwise"
        ]
      },
      "transfer_within_network": {
        "allow": "Yes",
        "transfer_mapping": [
          {
            "from_role": "01001",
            "to_role": "01002"
          },
          {
            "from_role": "01001",
            "to_role": "01003"
          }
        ]
      },
      "withdrawn_tokens_from_network": {
        "allow": "Yes"
      }
  }
}
```

- **케어 서클 (care\_circle)**

케어.서클(Care Circle)은 사용자가 가까운 케어.월렛 홀더, 공급자 및 관리 코디네이터와 연결할 수 있도록 하는 환자 중심의 관리 기능이다. 

이번 섹션은 케어.프로토콜과 케어 서클 사용 권한에 대한 구성이다. 

|필드 이름|값 유형|설명|
| :- | :- | :- |
|role\_allow|배열|<p>1. 케어 서클에 참가를 허용하는 역할</p><p>2. 필수</p>|
|journeys\_allow|배열|<p>1. 케어 서클과 공유를 허용하는 경로.</p><p>2. 필수</p>|

```json
{
  "care_circle": {
      "role_allow": [
        "01001",
        "01002",
        "01003"
      ],
      "journeys_allow": [
        "02001",
        "02002"
      ]
    }
}
```

- **케어 원장 (care\_ledger)**

이번 섹션은 케어.프로토콜은 에 게시해야 하는 이벤트 구성에서 케어 원장 (블록체인)부분이다. 

|필드 이름|값 유형|설명|
| :- | :- | :- |
|journeys\_allow\_to\_publish|문자열|<p>1. 케어 원장의 발행을 허용하는 경로. </p><p>2. 필수</p>|
|excluded\_journeys|배열|<p>1. 케어 원장 발행을 허용하지 않는 경로. </p><p>2. 필수</p>|
|journey\_wise\_events|JSON 값|<p>1. 케어 원장에 발행할 수 있는 경로와 이벤트를 나열한다. </p><p>2. 필수</p>|

```json
{
  "care_ledger": {
      "journeys_allow_to_publish": "All",
      "excluded_journeys": [
        "02003",
        "02009"
      ],
      "journey_wise_events": [
        {
          "journey": "02001",
          "events": [
            "04002",
            "04003"
          ]
        },
        {
          "journey": "02002",
          "events": [
            "04005",
            "04006"
          ]
        }
      ]
    
}
```



- **볼트 (vault)**

이번 섹션은 케어.프로토콜을 통해 작성자는 해결에서 볼트 저장소 요구 사항을 구성할 수 있다. 케어.볼트(Care.Vault)는 케어.월렛 홀더와 노드의 의해 100% 제어되는 로컬 내장형으로 볼트는 불변성과 감사성을 갖춘 분산형 데이터이다. 


|필드 이름|값 유형|설명|
| :- | :- | :- |
|backup\_options|JSON 값|<p>1. 본 네트워크에 대한 백업 옵션.</p><p>&emsp;a. 무료</p><p>&emsp;b. 업그레이드 </p><p>2. 필수</p>|
|upgrade\_options|JSON 값|<p>1. 본 네트워크에 대한 업데이트 옵션 리스트.</p><p>&emsp;a. 백업 사이즈 (Backup\_Size)</p><p>&emsp;b. 업데이트 비용(Upgrade\_Cost)</p><p>2. 필수</p>|

```json
{
  "vault": {
      "backup_options": {
        "free": "yes",
        "upgrade": "Yes"
      },
      "upgrade_options": {
        "tier_1": {
          "backup_size": "100GB",
          "upgrade_cost": "100 SOLVE/MONTH"
        },
        "tier_2": {
          "backup_size": "200GB",
          "upgrade_cost": "200 SOLVE/MONTH"
        }
      }
    }
}
```

- **지리적 가용성 (geographic\_availability)**

이번 섹션은 케어.프로토콜은 네트워크의 가용성을 정의한다. 국가별로 지역을 구성할 수 있도록  프로토콜의 지오 좌표를 기반으로 지오펜스(geo fence)를 지원할 수 있다. 


|필드 이름|값 유형|설명|
| :- | :- | :- |
|network|문자열|<p>1. 네트워크 이름. </p><p>2. 필수</p>|
|countries|배열|<p>3. 본 네트워크가 사용 가능한 국가 목록.</p><p>4. 필수</p>|
|countries\_excluded|배열|<p>1. 본 네트워크가 사용 불가능한 국가 목록. </p><p>2. 필수</p>|

```json
{
  "geographic_availability": {
      "countries": [
        "India",
        "USA"
      ],
      "countries_excluded": [
        "Australia",
        "UK"
      ]
    }
}
```
