import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

@app.message("hello")
def message_hello(message, say):
    say(f"Hey there <@{message['user']}>!")

@app.event("message")
def handle_message_events(body, logger):
    logger.info

@app.event("app_mention")
def event_test(event, say):
    message_text = event["text"]
    say ({"text": "Thank you for your query. I will now go and retrieve your answer, this can take up to x amount of time."})

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

    say({'text': "Hi there! This is the OpenAI answer I found in response to your question:\n\n" + message_text + '\n\n I am however just a bot. If your question was not answered satisfactorily, please select the relevant box.'})
        # Send a message with buttons asking for feedback
    say(
            {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Please select an option for how satisfied with the provided answer:",
                        },
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "This has resolved my query"},
                                "value": "yes",
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "This has not resolved my query"},
                                "value": "no",
                            },
                        ],
                    },
                ]
            }
        )


# Handle button clicks

@app.action("lM8iX")
def handle_some_action(ack, body, client, logger):
    ack()
    url = 'https://yourethemannowdog.ytmnd.com/'
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

@app.action("QaGUi")
def handle_some_action(ack, body, client, logger):
    ack()
    client.chat_postMessage(
        channel = body['container']['channel_id'],
        text = 'Thank you for using the powerful app service! If you have any further feedback on this service, please leave it as a reply to this thread. Our team will review all feedback to improve the service.'
    )
    logger.info(body)    

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()