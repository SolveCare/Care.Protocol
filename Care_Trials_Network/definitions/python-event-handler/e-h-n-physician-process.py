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
        self.index = 'sponsor_info'

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
        
    def send_submit_answers_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'Your sponsor search details have been successfully submitted.')
        
    def sponsor_match_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'You have a new sponsor match. Check your matches')    
            
    def handle(self) -> Map:
        print("Custom event handler")
        
        result = HashMap(self.arguments)
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(self.node.info().getScAddress()).build())
        self.send_submit_answers_notification()

        vault_data = self.vault.search('PHYSICIAN_ANSWERS', vault_filter)
        print("VaultData",vault_data)

        country = self.event_payload.get('Country')
        specialization = self.event_payload.get('specialization')
        experienceYears = self.event_payload.get('experienceYears')
        trialsConducted = self.event_payload.get('trialsConducted')
        phaseInterested = self.event_payload.get('phaseInterested')

        import re

        print("Phys Dataaaaaaaa",country, specialization, experienceYears, trialsConducted, phaseInterested)

       
        query = {
            "bool": {
                "must": []
         }  
        }
 
        
        print("Qqqq1", query)

        # Check if gender is not None
        query["bool"]["must"].append({
                "query_string": {
                 "query": f"(Country:{country})"
                }
            })
            
        query["bool"]["must"].append({
                "query_string": {
                 "query": f"(specialization:{specialization})"
                }
            })    
        query["bool"]["must"].append({
                "query_string": {
                 "query": f"(experienceYears:{experienceYears})"
                }
            })  
        query["bool"]["must"].append({
                "query_string": {
                 "query": f"(trialsConducted:{trialsConducted})"
                }
            })  
        query["bool"]["must"].append({
                "query_string": {
                 "query": f"(phaseInterested:{phaseInterested})"
                }
            })  
        

        print("QQQUERY",query)
        #cdn_data = self.cdn.raw_search(0, 1,query)
        cdn_data = self.cdn.raw_search('sponsor_info', 0, 100, query)

        print("CDN 1",cdn_data)
        
        
        country_filter = SimpleQueryBuilder.eq('Country', country)
        specialization_filter = SimpleQueryBuilder.eq('specialization', specialization)
        experienceYears_filter = SimpleQueryBuilder.eq('experienceYears', experienceYears)
        trialsConducted_filter = SimpleQueryBuilder.eq('trialsConducted', trialsConducted)
        phaseInterested_filter = SimpleQueryBuilder.eq('phaseInterested', phaseInterested)
        
        cdn_data = self.cdn.find_all('sponsor_info', SimpleQueryBuilder.aand(country_filter, specialization_filter, experienceYears_filter, trialsConducted_filter, phaseInterested_filter))

        print("CDN 2",cdn_data)

        archived_filter = List.of(EqualitySearchFilter.builder().fieldName("archived").value("false").build())

        archived_data = self.vault.search('SPONSORS', archived_filter)
        for item in archived_data:
            filterById = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(item.get('transactionalGuid')).build())
            item.put("archived", "true")
            archived = self.vault.update('SPONSORS', filterById, item, False)
            print("ARCHIVED TRIAL", archived)

        print("TRIAL List")
        import math


        for row in cdn_data:
            self.sponsor_match_notification()
            
            Loc= row.getData().get('Location')
            print("tttrialidddloc",Loc)

            sponsors = {

            # enrich with data from search response
            "Country": row.getData().get('Country'),
            "specialization": row.getData().get('specialization'),
            
            "experienceYears": row.getData().get('experienceYears'),
            "trialsConducted": row.getData().get('trialsConducted'),
            "phaseInterested": row.getData().get('phaseInterested'),
            "SponsorID": row.getData().get('SponsorID'),

            # enrich with runtime data
            "createdAt": self.current_milli_time(),
            "senderNodeAddress": self.node.info().getScAddress(),
            "transactionalGuid": str(uuid.uuid1()),
            
            "sponsorStatus": "NEW"
        }

            print("sponsorssss",sponsors)
            self.vault.save('SPONSORS', sponsors)
        

        return result


def execute(context: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler physician process]: {context}')
    result = CustomPythonEventHandler(context).handle()
    return result
