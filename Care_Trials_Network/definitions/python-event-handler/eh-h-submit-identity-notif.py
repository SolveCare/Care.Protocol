import java

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.event_payload = context.getEvent().getPayload()
        self.context = context

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def send_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'You have successfully submitted an identity for review to the nurse.')

    def handle(self) -> Map:
        result = HashMap(self.arguments)

        self.send_notification()
        print("Notification sent!")

        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-submit-identity-notif]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
