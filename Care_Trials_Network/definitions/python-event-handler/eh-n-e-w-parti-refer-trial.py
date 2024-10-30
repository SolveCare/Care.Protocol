from abc import ABC, abstractmethod

import java

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

    def find_node_by_public_key(self, public_key) -> Map:
        provider = self.context.getNetworkInfoProvider()
        node = self.find_own_node()
        network_id = node.getNetworkId()
        role_id = node.getNodeRoleId()
        print(f'Try to find node in network: {network_id} with role: {role_id} and public key: {public_key} ')
        return provider.searchFirstNode(network_id, None, None, public_key, role_id)


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
            'You have referred to Care. Wallet user by sharing the trial information.')

    def save_refer_to_cdn(self, recipient_sc_address: str):
        cdn_data = {
            'senderNodeAddress': self.sender_node_address,
            'recipientPublicKey': self.event_payload.get('recipientPublicKey'),
            'recipientScAddress': recipient_sc_address,
            'CampaignId': self.event_payload.get('CampaignId'),
            'CampaignType': self.event_payload.get('CampaignType'),
            'SiteID': self.event_payload.get('SiteID'),
            'TrialID': self.event_payload.get('TrialID'),
            'TrialName': self.event_payload.get('TrialName'),
            "BriefSummary" : self.event_payload.get('BriefSummary'),        

        }

        response = self.cdn.save('trials_refers', cdn_data)
        print(f'[saved]: {cdn_data} to trials_refers with id {response.getId()}')

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        result.remove('recipientPublicKey')
        result.put('SiteID', self.event_payload.get('SiteID'))
        recipient_public_key = self.event_payload.get('recipientPublicKey')
        recipient_node = self.network.find_node_by_public_key(recipient_public_key)
        recipient_sc_address = recipient_node.get("scAddress")
        recipient_ec_key = recipient_node.get("ecPublicKey")
        print(f'Found recipient node scAddress: {recipient_sc_address}, ec_key {recipient_ec_key}')
        if recipient_sc_address and recipient_ec_key:
            print(f'Add {recipient_sc_address} to ContactList')
            provider = self.context.getContactPairProvider()
            provider.addContact(recipient_sc_address, recipient_ec_key)

        self.save_refer_to_cdn(recipient_sc_address)

        self.context.initRecipientAddress(recipient_sc_address)

        self.send_notification()
        print("notification sent!")
        print('Execution done')
        return result


def execute(context: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {context}')
    result = CustomPythonEventHandler(context).handle()
    return result
