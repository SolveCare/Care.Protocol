import java

from abc import ABC, abstractmethod
from datetime import datetime

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
        questions_data_list = self.vault.search_pageable('PROFILING_QUESTIONS_SA', vault_filter, pagination)
        print(f'Found {len(questions_data_list)} records of PROFILING_QUESTIONS_SA')
        return questions_data_list
    
    def save_sa_answers(self, questions_data: Map):
        date = self.format_to_date_short(questions_data.get('createdAt'))
        print("SA answers date:", date)
        sa_answers = {
            'DPP': questions_data.get('DPP'),
            'InstitutionName': questions_data.get('InstitutionName'),
            'AffiliationAddress': questions_data.get('AffiliationAddress'),
            'EstablishedYear': questions_data.get('EstablishedYear'),
            'TypeOfAffiliation': questions_data.get('TypeOfAffiliation'),
            'InstitutionDescription': questions_data.get('InstitutionDescription'),
            'TrialsDescription': questions_data.get('TrialsDescription'),
            'Website': questions_data.get('Website'),
            'Email': questions_data.get('Email'),
            'Phone' : questions_data.get('Phone'),
            'transactionalGuid': questions_data.get('transactionalGuid'),
            'Date': date,
            'senderNodeAddress': questions_data.get('senderNodeAddress')
        }

        print("saving SA", sa_answers)
        self.cdn.save('site_admin_prof_ques', sa_answers)
        print("site_admin_prof_ques saved", sa_answers)



    def handle(self) -> Map:
        result = HashMap(self.arguments)

        questions_data_list = self.find_questions_data()

        questions_data = questions_data_list[0]
        
        print("save SA answers-->")
        self.save_sa_answers(questions_data)

        print('Execution done')
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler save SA profiling guestion question to cdn ]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
