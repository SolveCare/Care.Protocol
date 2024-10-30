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
        print("Custom event handler budddgettt lead skip")

        result = HashMap(self.arguments)

        print("AdminAddress", self.event_payload.get("AdminAddress"))
        admin_address = self.event_payload.get("AdminAddress")
        print("Adminnnn", admin_address)

        vault_filter = List.of(
            EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(admin_address).build())
        print("senderNodeAddress vault_filter", vault_filter)

        vault_budget = self.vault.search('BUDGET', vault_filter)
        print("senderNodeAddress vault_budget", vault_budget)

        amount_spent = 50

        if vault_budget:
            print("inside if ")
            for item in vault_budget:
                print("total_expensesss ", item.getOrDefault('total_expenses', 0))
                print("remaining_budgett ", item.getOrDefault('remaining_budget', 0))
                print("scnodeaddresss ", item.getOrDefault('senderNodeAddress', 0))

                data = {
                    "total_expenses": item.getOrDefault('total_expenses', 0) + amount_spent,
                    "remaining_budget": item.getOrDefault('remaining_budget', 0) - amount_spent,
                }
                print("data ", data)
                self.vault.update('BUDGET', vault_filter, data, False)
                print("UPDATED !")

        else:
            print("inside else ")
            data = {
                "total_expenses": 50,
                "remaining_budget": -50,
            }

            print("data", data)
            self.vault.save('BUDGET', data)

        result.putAll(self.event_payload)
        print("result", result)

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
