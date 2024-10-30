import java

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")

SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
QueryCondition = java.type('care.solve.node.core.model.cdn.QueryCondition')
QueryConditions = java.type('care.solve.node.core.model.cdn.QueryConditions')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def raw_search(self, indices: str, from_row, num_rows, search_request) -> List:
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


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.event_payload = context.getEvent().getPayload()
        self.cdn = CDN(context)
        self.vault = Vault(context)

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        trial_filter = List.of(
            EqualitySearchFilter.builder().fieldName("SiteID").value(self.event_payload.get("SiteID")).build())
        existing_trials = self.vault.search('TRIALS', trial_filter)
        throw_next_event = False
        if len(existing_trials) == 1:
            existing_trial = existing_trials[0]
            result.put("transactionalGuid", existing_trial.get("transactionalGuid"))
            existing_trial_status = existing_trial.get('trialStatus')
            if existing_trial_status == 'NEW':
                throw_next_event = True
                existing_trial.put('trialStatus', 'SAVED')
                existing_trial.put('status', 'LIKED')                
                self.vault.update('TRIALS', trial_filter, existing_trial, False)
                existing_trial.put('status', 'LIKED')
                
        result.put('throwNextEvent', throw_next_event)
        result.putAll(self.event_payload)
        print("result", result)

        # self.cdn.save('campaigns-likes', result)
        # print(f"CDN Save to 'campaigns-likes': {result}")
        self.cdn.save('trials_likes', result)
        print(f"CDN Save to 'trials_likes': {result}")

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [e-w-broad-matching rare]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
