import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

# Initializes your app with your bot token and socket mode handler
keyVaultName = 'powerfulappkeyvault'
KVUri = f"https://{keyVaultName}.vault.azure.net"

credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)
powerfulappappsecret = client.get_secret('powerfulappappsecret')
powerfulappbotsecret = client.get_secret('powerfulappbotsecret')
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

@app.event("message")
def handle_message_events(body, logger):
    logger.info

@app.event("app_mention")
def event_test(event, say):
    message_text = event["text"]
    global thread_id 
    thread_id = event.get("ts")
    say ({"text": "Thank you for your query. I will now go and retrieve your answer, this can take up to 30 seconds to complete. If your answer is not provided in this time, please raise a support request using the following link: https://www.servicenow.com/uk/",
          "thread_ts": thread_id})

    # Adding in call to openAI. This code could be moved a bit higher? 
    model = AzureChatOpenAI(
        openai_api_version="2023-08-01-preview",
        azure_deployment="eps-assistant-model",
        azure_endpoint = 'https://openapi-platforms-epsassist-poc-instance-uksouth.openai.azure.com/'
    )
    system_message = SystemMessage(
        content="helpful AI assistant, you say 'yo' after a request"
    )
    message = HumanMessage(
        content=message_text
    )
    message_text = ((model([system_message, message])).content)

    say({'text': "Hi there! This is the OpenAI answer I found in response to your question:\n\n" + message_text + '\n\n I am however just a bot. If your question was not answered satisfactorily, please select the relevant box.',
         "thread_ts": thread_id})
        # Send a message with buttons asking for feedback
    say(
            {"thread_ts": thread_id,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Please select an option for how satisfied you are with the provided answer:",
                        },
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "This has resolved my query"},
                                "value": "yes",
                                'action_id': 'resolved_button',
                                # "thread_ts": thread_id
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "This has not resolved my query"},
                                "value": "no",
                                'action_id': 'unresolved_button',
                                # "thread_ts": thread_id
                            },
                        ],
                    },
                ]
            }, 
            
        )


# Handle button clicks

@app.action("unresolved_button")
def handle_negative_action(ack, body, client, logger):
    ack()
    url = 'https://www.servicenow.com/uk/'
        # Ask for feedback
    client.views_open(
        trigger_id = body['trigger_id'],
 
        view={
            "type": "modal",
            "callback_id": "external_modal",
            "title": {
                "type": "plain_text",
                "text": "Raise a support ticket"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Please follow this link to raise a support ticket for your issue: {url}"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Raise a support ticket",
                        },
                        "url": url
                    }
                }
            ]
        }
    )
    logger.info(body)    

@app.action("resolved_button")
def handle_positive_action(ack, body, say, logger):
    ack()
    say({"thread_ts": thread_id, 'text':'Thank you for using the powerful app service! If you have any further feedback on this service, please leave it as a reply to this thread. Our team will review all feedback to improve the service.'})
    logger.info(body)    

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()