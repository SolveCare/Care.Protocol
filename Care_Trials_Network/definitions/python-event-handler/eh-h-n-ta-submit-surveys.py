
from abc import ABC, abstractmethod
from datetime import datetime

import java

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
Pagination = java.type('care.solve.node.core.model.query.Pagination')
Sorting = java.type('care.solve.node.core.model.query.Sorting')

SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def find_all(self, indices: str, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(indices, parameters)

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)


class Vault:

    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def save(self, collection: str, data: Map) -> Map:
        vault = self.context.getVaultStorage(collection)
        guid = vault.save(data)
        return vault.getByGuid(guid)

    def search(self, collection: str, criteria: List) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria)

    def search_pageable(self, collection: str, criteria: List, pagination: Pagination) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria, pagination)

    def count(self, collection: str, criteria: List) -> int:
        vault = self.context.getVaultStorage(collection)
        return vault.count(criteria)


class Node:

    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def info(self) -> NodeInfo:
        return self.context.getNodeInfo()


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.sender_node_address = context.getEvent().getFrom()
        self.event_payload = context.getEvent().getPayload()
        self.vault = Vault(context)
        self.cdn = CDN(context)
        self.node = Node(context)
        self.context = context

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    @staticmethod
    def format_to_date_short(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt_object.date().isoformat()
  

    def find_questions_data(self) -> List:
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        pagination = Pagination.of(0, 2, Sorting.desc('createdAt'))
        questions_data_list = self.vault.search_pageable('SURVEY_QUESTIONS_TA', vault_filter, pagination)
        print(f'Found {len(questions_data_list)} records of SURVEY_QUESTIONS_TA')
        return questions_data_list


    def save_ta_answers(self, questions_data: Map):
        date = self.format_to_date_short(questions_data.get('createdAt'))
        print("TA answers date:", date)
        ta_answers = {
            "D1DesignQ1": questions_data.get("D1DesignQ1"),
            "D1DesignQ2": questions_data.get("D1DesignQ2"),
            "D1DesignQ3": questions_data.get("D1DesignQ3"),
            "D1DesignQ4": questions_data.get("D1DesignQ4"),
            "D1DesignQ5": questions_data.get("D1DesignQ5"),
            "D1DesignQ6": questions_data.get("D1DesignQ6"),
            "D1DesignQ7": questions_data.get("D1DesignQ7"),
            "D1ProductDevelopmentQ1": questions_data.get("D1ProductDevelopmentQ1"),
            "D1ProductDevelopmentQ2": questions_data.get("D1ProductDevelopmentQ2"),
            "D1ProductDevelopmentQ3": questions_data.get("D1ProductDevelopmentQ3"),
            "D1ProductDevelopmentQ4": questions_data.get("D1ProductDevelopmentQ4"),
            "D1ProductDevelopmentQ5": questions_data.get("D1ProductDevelopmentQ5"),
            "D1ProductDevelopmentQ6": questions_data.get("D1ProductDevelopmentQ6"),
            "D1ProductDevelopmentQ7": questions_data.get("D1ProductDevelopmentQ7"),
            "D1ProtocolOperationQ1": questions_data.get("D1ProtocolOperationQ1"),
            "D1ProtocolOperationQ2": questions_data.get("D1ProtocolOperationQ2"),
            "D1ProtocolOperationQ3": questions_data.get("D1ProtocolOperationQ3"),
            "D1ProtocolOperationQ4": questions_data.get("D1ProtocolOperationQ4"),
            "D1ProtocolOperationQ5": questions_data.get("D1ProtocolOperationQ5"),
            "D1DataManagementQ1": questions_data.get("D1DataManagementQ1"),
            "D1DataManagementQ2": questions_data.get("D1DataManagementQ2"),
            "D1DataManagementQ3": questions_data.get("D1DataManagementQ3"),
            "D1DataManagementQ4": questions_data.get("D1DataManagementQ4"),
            "D1AnalysisQ1": questions_data.get("D1AnalysisQ1"),
            "D1AnalysisQ2": questions_data.get("D1AnalysisQ2"),
            "D1AnalysisQ3": questions_data.get("D1AnalysisQ3"),
            "D2EthicsQ1": questions_data.get("D2EthicsQ1"),
            "D2EthicsQ2": questions_data.get("D2EthicsQ2"),
            "D2EthicsQ3": questions_data.get("D2EthicsQ3"),
            "D2EthicsQ4": questions_data.get("D2EthicsQ4"),
            "D2EthicsQ5": questions_data.get("D2EthicsQ5"),
            "D2EthicsQ6": questions_data.get("D2EthicsQ6"),
            "D2EthicsQ7": questions_data.get("D2EthicsQ7"),
            "D2EthicsQ8": questions_data.get("D2EthicsQ8"),
            "D2EthicsQ9": questions_data.get("D2EthicsQ9"),
            "D2ClinicalPracticeQ1": questions_data.get("D2ClinicalPracticeQ1"),
            "D2ClinicalPracticeQ2": questions_data.get("D2ClinicalPracticeQ2"),
            "D2ClinicalPracticeQ3": questions_data.get("D2ClinicalPracticeQ3"),
            "D2ClinicalPracticeQ4": questions_data.get("D2ClinicalPracticeQ4"),
            "D2ClinicalPracticeQ5": questions_data.get("D2ClinicalPracticeQ5"),
            "D2ClinicalPracticeQ6": questions_data.get("D2ClinicalPracticeQ6"),
            "D2ClinicalPracticeQ7": questions_data.get("D2ClinicalPracticeQ7"),
            "D2ClinicalPracticeQ8": questions_data.get("D2ClinicalPracticeQ8"),
            "D2ClinicalPracticeQ9": questions_data.get("D2ClinicalPracticeQ9"),
            "D2ClinicalPracticeQ10": questions_data.get("D2ClinicalPracticeQ10"),
            "D2RiskSafetyQ1": questions_data.get("D2RiskSafetyQ1"),
            "D2RiskSafetyQ2": questions_data.get("D2RiskSafetyQ2"),
            "D2RiskSafetyQ3": questions_data.get("D2RiskSafetyQ3"),
            "D2RiskSafetyQ4": questions_data.get("D2RiskSafetyQ4"),
            "D2QualityAssuranceQ1": questions_data.get("D2QualityAssuranceQ1"),
            "D2QualityAssuranceQ2": questions_data.get("D2QualityAssuranceQ2"),
            "D2QualityAssuranceQ3": questions_data.get("D2QualityAssuranceQ3"),
            "D3OversightQ1": questions_data.get("D3OversightQ1"),
            "D3OversightQ2": questions_data.get("D3OversightQ2"),
            "D3OversightQ3": questions_data.get("D3OversightQ3"),
            "D3OversightQ4": questions_data.get("D3OversightQ4"),
            "D3OversightQ5": questions_data.get("D3OversightQ5"),
            "D3RegulationsQ1": questions_data.get("D3RegulationsQ1"),
            "D3RegulationsQ2": questions_data.get("D3RegulationsQ2"),
            "D3RegulationsQ3": questions_data.get("D3RegulationsQ3"),
            "D3RegulationsQ4": questions_data.get("D3RegulationsQ4"),
            "D3RegulationsQ5": questions_data.get("D3RegulationsQ5"),
            "D3RegulationsQ6": questions_data.get("D3RegulationsQ6"),
            "D3RegulationsQ7": questions_data.get("D3RegulationsQ7"),
            "D3StudyCommunicationsQ1": questions_data.get("D3StudyCommunicationsQ1"),
            "D3StudyCommunicationsQ2": questions_data.get("D3StudyCommunicationsQ2"),
            "D3StudyCommunicationsQ3": questions_data.get("D3StudyCommunicationsQ3"),
            "D3StudyCommunicationsQ4": questions_data.get("D3StudyCommunicationsQ4"),
            "D3StaffManagementQ1": questions_data.get("D3StaffManagementQ1"),
            "D3StaffManagementQ2": questions_data.get("D3StaffManagementQ2"),
            "D3StaffManagementQ3": questions_data.get("D3StaffManagementQ3"),
            "D3StaffManagementQ4": questions_data.get("D3StaffManagementQ4"),
            "D3StaffManagementQ5": questions_data.get("D3StaffManagementQ5"),
            "D3StaffManagementQ6": questions_data.get("D3StaffManagementQ6"),
            "D3ResourceManagementQ1": questions_data.get("D3ResourceManagementQ1"),
            "D3ResourceManagementQ2": questions_data.get("D3ResourceManagementQ2"),
            "D3ResourceManagementQ3": questions_data.get("D3ResourceManagementQ3"),
            "D3OperationsQ1": questions_data.get("D3OperationsQ1"),
            "D3OperationsQ2": questions_data.get("D3OperationsQ2"),
            "D3OperationsQ3": questions_data.get("D3OperationsQ3"),
            "D3OperationsQ4": questions_data.get("D3OperationsQ4"),
            "D3OperationsQ5": questions_data.get("D3OperationsQ5"),
            "D4LeadershipManagementQ1": questions_data.get("D4LeadershipManagementQ1"),
            "D4LeadershipManagementQ2": questions_data.get("D4LeadershipManagementQ2"),
            "D4LeadershipManagementQ3": questions_data.get("D4LeadershipManagementQ3"),
            "D4LeadershipManagementQ4": questions_data.get("D4LeadershipManagementQ4"),
            "D4LeadershipManagementQ5": questions_data.get("D4LeadershipManagementQ5"),
            "D4InterpersonalSkillsQ1": questions_data.get("D4InterpersonalSkillsQ1"),
            "D4InterpersonalSkillsQ2": questions_data.get("D4InterpersonalSkillsQ2"),
            "D4CommunicationEngagementQ1": questions_data.get("D4CommunicationEngagementQ1"),
            "D4CommunicationEngagementQ2": questions_data.get("D4CommunicationEngagementQ2"),
            "D4CommunicationEngagementQ3": questions_data.get("D4CommunicationEngagementQ3"),
            "D4CommunicationEngagementQ4": questions_data.get("D4CommunicationEngagementQ4"),
            "D4CommunicationEngagementQ5": questions_data.get("D4CommunicationEngagementQ5"),
            "D4CommunicationEngagementQ6": questions_data.get("D4CommunicationEngagementQ6"),
            "isAnswered": questions_data.get("isAnswered"),
            "isNotAnswered": questions_data.get("isNotAnswered"),
            "IssuedOn": questions_data.get("IssuedOn"),
            "transactionalGuid": questions_data.get("transactionalGuid"),
            "Date": date,
            "senderNodeAddress": questions_data.get("senderNodeAddress")
        }

        print("saving TA info", ta_answers)
        self.cdn.save('trial_admin_survey', ta_answers)
        print("trial_admin_survey saved", ta_answers)


    def handle(self) -> Map:
        result = HashMap(self.arguments)

        questions_data_list = self.find_questions_data()

        questions_data = questions_data_list[0]
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'Your answers has been successfully submitted.')
        print("notification sent!")
        
        print("save TA answers-->")
        self.save_ta_answers(questions_data)

        print('Execution done')
        return result


def execute(context: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler save TA survey question to cdn ]: {context}')
    result = CustomPythonEventHandler(context).handle()
    return result
