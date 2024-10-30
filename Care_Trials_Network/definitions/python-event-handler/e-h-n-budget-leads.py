import java

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
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


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.event_payload = context.getEvent().getPayload()
        self.vault = Vault(context)

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):
    def handle(self) -> Map:
        print("Custom event handler budddgettt buy leadss")

        result = HashMap(self.arguments)

        print("SiteIDDDD", self.event_payload.get("SiteID"))

        vault_filter = List.of(
            EqualitySearchFilter.builder().fieldName("SiteID").value(self.event_payload.get("SiteID")).build())
        print("siteidddd vault_filter", vault_filter)

        vault_budget = self.vault.search('BUDGET', vault_filter)
        print("siteidddd vault_budget", vault_budget)

        amount_spent = 4950

        if vault_budget:
            print("inside if ")
            total_expenses = vault_budget[0].getOrDefault('total_expenses', 0)
            budget = vault_budget[0].getOrDefault('Budget', 0)
            print("true ", total_expenses, budget)

        else:
            print("inside else ")
            total_expenses = 0
            budget = 0
            print("false ", total_expenses, budget)

        print("total_expenses 1:", total_expenses)
        total_expenses += amount_spent

        print("total_expenses 2:", total_expenses)
        print("budget:", budget)

        remaining_budget = budget - total_expenses
        print("remaining_budget:", remaining_budget)

        from datetime import datetime

        # Get the current date and time
        current_datetime = datetime.now()

        # Extract the date portion
        current_date = current_datetime.date()
        formatted_date = current_date.strftime("%d-%m-%Y")

        updated_date = formatted_date
        print("updated_date", updated_date)

        data = {
            "SiteID": self.event_payload.get('SiteID'),
            "total_expenses": total_expenses,
            "remaining_budget": remaining_budget,
        }

        print("data", data)

        if vault_budget:
            self.vault.update('BUDGET', vault_filter, data, False)
        else:
            self.vault.save('BUDGET', data)

        result.putAll(self.event_payload)
        print("result", result)

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
