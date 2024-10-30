from abc import ABC, abstractmethod

import java
from datetime import datetime

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
NodeInfo = java.type('care.solve.node.core.model.NodeInfo')

SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)


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

    def send_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'Your request for activation code has been successfully sent.')

    @staticmethod
    def format_to_date(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt_object.isoformat()

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        print('eh-n-e-w-request-code.py start')
        print('createdAt', self.event_payload.get('createdAt'))

        creadetAt = self.event_payload.get('createdAt')

        if creadetAt:
            date = self.format_to_date(creadetAt)
        else:
            current_time = datetime.now()
            date = current_time.strftime('%d-%m-%Y')

        cdn_data = {
            'senderNodeAddress': self.sender_node_address,
            'NCTid': self.event_payload.get('ID'),
            'email': self.event_payload.get('email'),
            'date': date,
        }

        response = self.cdn.save('requests_code', cdn_data)
        print(f'[saved]: {cdn_data} to requests_code with id {response.getId()}')

        self.send_notification()
        print("Notification sent!")
        print('Execution done')
        return result


def execute(context: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {context}')
    result = CustomPythonEventHandler(context).handle()
    return result
