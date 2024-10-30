from abc import ABC, abstractmethod

import java
from datetime import datetime

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type('care.solve.node.core.model.NodeInfo')

SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')

class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)
    
    
    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def find_all(self, indices: str, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(indices, parameters)


class NetworkInfo:

    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_own_node(self) -> NodeInfo:
        return self.context.getNodeInfo()


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.sender_node_address = context.getEvent().getFrom()
        self.event_payload = context.getEvent().getPayload()
        self.network = NetworkInfo(context)
        self.context = context
        self.cdn = CDN(context)

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    @staticmethod
    def format_to_date(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt_object.isoformat()

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        print('eh-n-e-w-promo-code.py start')
        print('PromoCode', self.event_payload.get('PromoCode'))

        PromoCode = self.event_payload.get('PromoCode')
        reviewPayWith = self.event_payload.get('reviewPayWith')
        

        print('reviewPayWith', reviewPayWith)
        print('PromoCode', PromoCode)
        
        promo_details = self.cdn.find_all('promo_activities', SimpleQueryBuilder.eq('Code', PromoCode))
        print('promo_details',promo_details)
        
        promo_solve = promo_details[0].getData().get('TotalAmount')
        available_solve = promo_details[0].getData().get('AvailableAmount')

        if promo_solve <= available_solve:
            print("Enough SOLVE available")
            balance_solve = available_solve - promo_solve
            print("balance_solve", balance_solve)
            
        else:
            print("Enough SOLVE not available")
            
#        cdn_data = {
#            'senderNodeAddress': self.sender_node_address,
#            'NCTid': self.event_payload.get('ID'),
#            'email': self.event_payload.get('email')
#            }

#        response = self.cdn.save('requests_code', cdn_data)
#        print(f'[saved]: {cdn_data} to requests_code with id {response.getId()}')

#        print('Execution done')
        return result


def execute(context: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler promo code]: {context}')
    result = CustomPythonEventHandler(context).handle()
    return result