import math
import re
import time
import uuid
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

    def raw_search(self, indices, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(indices, from_row, num_rows, search_request)

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)


class Vault:

    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def save(self, collection: str, data: Map) -> Map:
        vault = self.context.getVaultStorage(collection)
        guid = vault.save(data)
        return vault.getByGuid(guid)

    def update(self, collection: str, criteria: List, data: Map, insert_if_absent: bool) -> Map:
        vault = self.context.getVaultStorage(collection)
        print(f'==> [CustomPythonEventHandler#d]: {data}')
        guid = vault.update(criteria, data, insert_if_absent)
        print(f'==> [CustomPythonEventHandler#d]: {guid}')
        return vault.getByGuid(guid)

    def search(self, collection: str, criteria: List) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria)

    def search_pageable(self, collection: str, criteria: List, pagination: Pagination) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria, pagination)

    def remove(self, collection: str, guid: str):
        vault = self.context.getVaultStorage(collection)
        vault.delete(guid)

    def remove_by_criteria(self, collection: str, criteria: List) -> int:
        vault = self.context.getVaultStorage(collection)
        return vault.delete(criteria)

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
    def current_milli_time():
        return round(time.time() * 1000)

    @staticmethod
    def format_to_date(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt_object.isoformat()

    @staticmethod
    def format_to_date_short(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt_object.date().isoformat()
  

    def find_questions_data(self) -> List:
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        pagination = Pagination.of(0, 2, Sorting.desc('createdAt'))
        questions_data_list = self.vault.search_pageable('PROFILING_QUESTIONS_PHYS', vault_filter, pagination)
        print(f'Found {len(questions_data_list)} records of PROFILING_QUESTIONS_PHYS')
        return questions_data_list



    def send_notifications(self, saved: int):
        if saved > 0:
            self.send_trials_found_notification(saved)
        else:
            self.send_trials_not_found_notification()



    def save_sponsor_answers(self, questions_data: Map):
        date = self.format_to_date_short(questions_data.get('createdAt'))
        print("sponsor answers date:", date)
        spons_answers = {
            'DPP': questions_data.get('DPP'),
            'FirstName': questions_data.get('FirstName'),
            'LastName': questions_data.get('LastName'),
            'Education': questions_data.get('Education'),
            'SpecializationField': questions_data.get('SpecializationField'),
            'InstitutionalAffiliation': questions_data.get('InstitutionalAffiliation'),
            'InstitutionAddress': questions_data.get('InstitutionAddress'),
            'orgAffiliation': questions_data.get('orgAffiliation'),
            'otherOrganization': questions_data.get('otherOrganization'),
            'PositionInstitution': questions_data.get('PositionInstitution'),
            'InstitutionDescription': questions_data.get('InstitutionDescription'),
            'ExperienceYears': questions_data.get('ExperienceYears'),
            'ExpertiseAreas': questions_data.get('ExpertiseAreas'),
            'ParticipationDescription': questions_data.get('ParticipationDescription'),
            'TitleYear': questions_data.get('TitleYear'),
            'recentRole': questions_data.get('recentRole'),
            'otherRecentRole': questions_data.get('otherRecentRole'),
            'Email': questions_data.get('Email'),
            'Phone' : questions_data.get('Phone'),
            'transactionalGuid': questions_data.get('transactionalGuid'),
            #'createdAt': questions_data.get('createdAt'),
            'Date': date
        }
        print("saving sponsor_info", spons_answers)
        self.cdn.save('physician_prof_ques', spons_answers)
        print("physician_prof_ques saved", spons_answers)


    def handle(self) -> Map:

        max_trials = 500

        result = HashMap(self.arguments)
        # List of all records from 6_QUESTIONS vault collection
        questions_data_list = self.find_questions_data()
        # Latest record from 6_QUESTIONS vault collection
        questions_data = questions_data_list[0]
        # self.context.getNotificationProvider().send(
        #     'Congratulations!',
        #     'Your Physician profiling answers have been successfully submitted.')
        # print("notification sent!")
        
        print("sponsor profiling answers-->")
        self.save_sponsor_answers(questions_data)

        print('Execution done')
        return result


def execute(context: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler save prof ques to cdn ]: {context}')
    result = CustomPythonEventHandler(context).handle()
    return result
