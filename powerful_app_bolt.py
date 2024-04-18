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
powerfulappappsecret = powerfulappappsecret.value

powerfulappbotsecret = client.get_secret('powerfulappbotsecret')
powerfulappbotsecret = powerfulappbotsecret.value

app = App(token=powerfulappbotsecret)

@app.event("message")
def handle_message_events(body, logger):
    logger.info

@app.event("app_mention")
def event_test(event, say):
    message_text = event["text"]
    # At the moment, I'm having to call this as a global variable. This needs changing for the 'handle_positive_action' function, I have so far been unable to pass the thread_id to respond on any other way, and cannot find a thread_id in the Ack object that triggers the positive action.
    global thread_id 
    thread_id = event.get("ts")
    # Change to the relevant way we want to handle failed calls. 
    awaiting_text = "Thank you for your query. I will now go and retrieve your answer, this can take up to 3 minutes to complete. If your answer is not provided in this time, please raise a support request using the following link: https://www.servicenow.com/uk/"
    say ({"text": awaiting_text,
          "thread_ts": thread_id})

    # Call to openAI. Will need to be updated once the deployed model is available, as it currently facing a generic openAI conversation
    # TODO: Add in ConversationChain library to maintain context/ask further Qs. Will need an if else loop looking at the thread_id, again will need to extract thread_id somehow, may add in buttons to continue the conversation, then to go to feedback.
    model = AzureChatOpenAI(
        openai_api_version="2023-08-01-preview",
        azure_deployment="eps-assistant-model",
        azure_endpoint = 'https://openapi-platforms-epsassist-poc-instance-uksouth.openai.azure.com/'
    )
    message = HumanMessage(
        content=message_text
    )
    ai_answer = ((model([message])).content)
    answer_text = f"Hi there! This is the OpenAI answer I found in response to your question:\n\n {ai_answer} \n\n I am however just a bot. If your question was not answered satisfactorily, please select the relevant box."

    say({'text': answer_text,
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
                                # Trying to add the thread ID as metadata on the button, in order for further extraction. 
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
    text = 'Thank you for using the powerful app service! If you have any further feedback on this service, please leave it as a reply to this thread. Our team will review all feedback to improve the service.'
    # TODO: As above, so below, extract the thread_id without relying on a global variable ideally. 
    say({"thread_ts": thread_id, 'text': text})
    logger.info(body)    

if __name__ == "__main__":
    SocketModeHandler(app, powerfulappappsecret).start()