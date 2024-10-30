
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
        questions_data_list = self.vault.search_pageable('SURVEY_QUESTIONS_SA', vault_filter, pagination)
        print(f'Found {len(questions_data_list)} records of SURVEY_QUESTIONS_SA')
        return questions_data_list


    def save_sa_answers(self, questions_data: Map):
        date = self.format_to_date_short(questions_data.get('createdAt'))
        print("TA answers date:", date)
        sa_answers = {
            "D1SpaceQ1": questions_data.get("D1SpaceQ1"),
            "D1SpaceQ2": questions_data.get("D1SpaceQ2"),
            "D1SpaceQ3": questions_data.get("D1SpaceQ3"),
            "D1SpaceQ4": questions_data.get("D1SpaceQ4"),
            "D1PathologyQ1": questions_data.get("D1PathologyQ1"),
            "D1PathologyQ2": questions_data.get("D1PathologyQ2"),
            "D1PathologyQ3": questions_data.get("D1PathologyQ3"),
            "D1PathologyQ4": questions_data.get("D1PathologyQ4"),
            "D1PharmacyQ1": questions_data.get("D1PharmacyQ1"),
            "D1DiagnosticQ1": questions_data.get("D1DiagnosticQ1"),
            "D1DiagnosticQ2": questions_data.get("D1DiagnosticQ2"),
            "D1DiagnosticQ3": questions_data.get("D1DiagnosticQ3"),
            "D1SpecServicesQ1": questions_data.get("D1SpecServicesQ1"),
            "D1SpecServicesQ2": questions_data.get("D1SpecServicesQ2"),
            "D1SpecServicesQ3": questions_data.get("D1SpecServicesQ3"),
            "D1StorageQ1": questions_data.get("D1StorageQ1"),
            "D1StorageQ2": questions_data.get("D1StorageQ2"),
            "D1StructureSuppQ1": questions_data.get("D1StructureSuppQ1"),
            "D1StructureSuppQ2": questions_data.get("D1StructureSuppQ2"),
            "D1StructureSuppQ3": questions_data.get("D1StructureSuppQ3"),
            "D1StructureSuppQ4": questions_data.get("D1StructureSuppQ4"),
            "D1StructureSuppQ5": questions_data.get("D1StructureSuppQ5"),
            "D1StructureSuppQ6": questions_data.get("D1StructureSuppQ6"),
            "D1StructureSuppQ7": questions_data.get("D1StructureSuppQ7"),
            "D1StructureSuppQ8": questions_data.get("D1StructureSuppQ8"),
            "D1StructureSuppQ9": questions_data.get("D1StructureSuppQ9"),
            "D1StructureSuppQ10": questions_data.get("D1StructureSuppQ10"),
            "D1ResourcesQ1": questions_data.get("D1ResourcesQ1"),
            "D1ResourcesQ2": questions_data.get("D1ResourcesQ2"),
            "D1ResourcesQ3": questions_data.get("D1ResourcesQ3"),
            "D1ResourcesQ4": questions_data.get("D1ResourcesQ4"),
            "D1SelfGrading": questions_data.get("D1SelfGrading"),
            "D2EthicsQ1": questions_data.get("D2EthicsQ1"),
            "D2EthicsQ2": questions_data.get("D2EthicsQ2"),
            "D2EthicsQ3": questions_data.get("D2EthicsQ3"),
            "D2QualityQ1": questions_data.get("D2QualityQ1"),
            "D2QualityQ2": questions_data.get("D2QualityQ2"),
            "D2QualityQ3": questions_data.get("D2QualityQ3"),
            "D2QualityQ4": questions_data.get("D2QualityQ4"),
            "D2SafetyQ1": questions_data.get("D2SafetyQ1"),
            "D2SafetyQ2": questions_data.get("D2SafetyQ2"),
            "D2SafetyQ3": questions_data.get("D2SafetyQ3"),
            "D2SafetyQ4": questions_data.get("D2SafetyQ4"),
            "D2TrainingQ1": questions_data.get("D2TrainingQ1"),
            "D2TrainingQ2": questions_data.get("D2TrainingQ2"),
            "D2TrainingQ3": questions_data.get("D2TrainingQ3"),
            "D2SelfGrading": questions_data.get("D2SelfGrading"),
            "D3PartnershipsQ1": questions_data.get("D3PartnershipsQ1"),
            "D3PartnershipsQ2": questions_data.get("D3PartnershipsQ2"),
            "D3PartnershipsQ3": questions_data.get("D3PartnershipsQ3"),
            "D3PartnershipsQ4": questions_data.get("D3PartnershipsQ4"),
            "D3PartnershipsQ5": questions_data.get("D3PartnershipsQ5"),
            "D3SponsorsQ1": questions_data.get("D3SponsorsQ1"),
            "D3SponsorsQ2": questions_data.get("D3SponsorsQ2"),
            "D3SponsorsQ3": questions_data.get("D3SponsorsQ3"),
            "D3GovernmentQ1": questions_data.get("D3GovernmentQ1"),
            "D3SelfGrading": questions_data.get("D3SelfGrading"),
            "D4BasicInfrastructureQ1": questions_data.get("D4BasicInfrastructureQ1"),
            "D4BasicInfrastructureQ2": questions_data.get("D4BasicInfrastructureQ2"),
            "D4TechnologiesQ1": questions_data.get("D4TechnologiesQ1"),
            "D4TechnologiesQ2": questions_data.get("D4TechnologiesQ2"),
            "D4TechnologiesQ3": questions_data.get("D4TechnologiesQ3"),
            "D4TechnologiesQ4": questions_data.get("D4TechnologiesQ4"),
            "D4TechnologiesQ5": questions_data.get("D4TechnologiesQ5"),
            "D4TechnologiesQ6": questions_data.get("D4TechnologiesQ6"),
            "D4TechnologiesQ7": questions_data.get("D4TechnologiesQ7"),
            "D4DataManagQ1": questions_data.get("D4DataManagQ1"),
            "D4DataManagQ2": questions_data.get("D4DataManagQ2"),
            "D4DataManagQ3": questions_data.get("D4DataManagQ3"),
            "D4DataManagQ4": questions_data.get("D4DataManagQ4"),
            "D4DataManagQ5": questions_data.get("D4DataManagQ5"),
            "D4SecurityQ1": questions_data.get("D4SecurityQ1"),
            "D4SecurityQ2": questions_data.get("D4SecurityQ2"),
            "D4SecurityQ3": questions_data.get("D4SecurityQ3"),
            "D4SelfGrading": questions_data.get("D4SelfGrading"),
            "isAnswered": questions_data.get("isAnswered"),
            "isNotAnswered": questions_data.get("isNotAnswered"),
            "IssuedOn": questions_data.get("IssuedOn"),
            "transactionalGuid": questions_data.get("transactionalGuid"),
            "Date": date,
            "senderNodeAddress": questions_data.get("senderNodeAddress")
        }

        print("saving SA info", sa_answers)
        self.cdn.save('site_admin_survey', sa_answers)
        print("trial_admin_survey saved", sa_answers)


    def handle(self) -> Map:
        result = HashMap(self.arguments)

        questions_data_list = self.find_questions_data()

        questions_data = questions_data_list[0]
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'Your answers has been successfully submitted.')
        print("notification sent!")
        
        print("save SA answers-->")
        self.save_sa_answers(questions_data)

        print('Execution done')
        return result


def execute(context: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler save SA survey question to cdn ]: {context}')
    result = CustomPythonEventHandler(context).handle()
    return result
