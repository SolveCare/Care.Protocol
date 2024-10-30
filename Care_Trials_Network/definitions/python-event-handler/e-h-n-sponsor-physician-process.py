import java
import math
import re
import time
import uuid
from datetime import datetime

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")


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
    
    def handle(self) -> Map:

        result = HashMap(self.arguments)

        sponsor_id = self.event_payload.get("SponsorID")
        guid = self.event_payload.get("transactionalGuid")
        print("transactionalGuid: ", guid)
        print("SponsorID: ", sponsor_id)

        sponsor_filter = List.of(
            #EqualitySearchFilter.builder().fieldName("SponsorID").value(self.node.info().getScAddress()).build(),
            EqualitySearchFilter.builder().fieldName("Country").value(self.event_payload.get("Country")).build())
        sponsor_data_list = self.vault.search('SPONSORS', sponsor_filter)
        print("sponsor_data_list: ", sponsor_data_list)

        if len(sponsor_data_list) == 0:
            print(f'No found sponsor with SponsorID: {sponsor_id}')
            return result

        sponsor_data = sponsor_data_list[0]
        print(f'Found sponsor: {sponsor_data}')

        sponsor = {
            "senderNodeAddress": self.sender_node_address,
            "physicianNodeAddress": self.event_payload.get("senderNodeAddress"),
            "transactionalGuid": self.event_payload.get("transactionalGuid"),
            
            "Country": self.event_payload.get('Country'),
            "specialization": self.event_payload.get('specialization'),

            "experienceYears": self.event_payload.get('experienceYears'),
            "trialsConducted": self.event_payload.get('trialsConducted'),
            "phaseInterested": self.event_payload.get('phaseInterested'),
            "SponsorID": self.event_payload.get('SponsorID'),
            #"PhysicianID": self.event_payload.get("sender_node_address"),

            # enrich with runtime data
            "createdAt": self.current_milli_time(),
            "senderNodeAddress": self.node.info().getScAddress(),            
            "sponsorStatus": "LIKED",
            "physicianStatus" : "BOUGHT"
        }

        print(f"Care.Trial: {sponsor}")
        sponsor_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(self.event_payload.get('transactionalGuid')).build())
        self.vault.update('SPONSORS', sponsor_filter, sponsor, True)
        self.vault.save('PHYSICIAN_SPONSOR', sponsor)

        return result



def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler physician-sponsor-process]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
