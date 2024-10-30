import java

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context
        self.index = 'trials-with-geo'

    def find_all(self, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(self.index, parameters)

    def find_first(self, parameters: SimpleQueryBuilder) -> SearchResponse:
        transaction_criteria = SimpleQueryBuilder.eq('_transaction_id',
                                                     self.context.getEvent().getPayload().get('transactionId'))
        return self.context.getCareDataNodeProvider().findFirst(self.index, SimpleQueryBuilder.aand(parameters,
                                                                                                    transaction_criteria))

    def raw_search(self, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(self.index, from_row, num_rows, search_request)


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.sender_node_address = context.getEvent().getFrom()
        self.event_payload = context.getEvent().getPayload()
        self.cdn = CDN(context)

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def handle(self) -> Map:
        result = HashMap(self.arguments)

        if self.event_payload:
            trial_id = self.event_payload.get("TrialID")
            print("CDN Query:", trial_id)
            trial_data_list = self.cdn.find_all(SimpleQueryBuilder.eq('NCTId', trial_id))
            total_sites = len(trial_data_list)

            print(f'Care.Trial sites: {trial_data_list}')
            print(f'sites counttt: {total_sites}')

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
