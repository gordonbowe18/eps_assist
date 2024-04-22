from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain_openai import AzureChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryMemory
from langchain_community.callbacks import get_openai_callback
import random
from datetime import date


# Initializes your app with your bot token and socket mode handler
keyVaultName = 'powerfulappkeyvault'
KVUri = f"https://{keyVaultName}.vault.azure.net"

credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)
powerfulappappsecret = client.get_secret('powerfulappappsecret')
powerfulappappsecret = powerfulappappsecret.value

powerfulappbotsecret = client.get_secret('powerfulappbotsecret')
powerfulappbotsecret = powerfulappbotsecret.value

nested_dict = {}

app = App(token=powerfulappbotsecret)

model = AzureChatOpenAI(
    openai_api_version="2023-08-01-preview",
    azure_deployment="eps-assistant-model",
    azure_endpoint = 'https://openapi-platforms-epsassist-poc-instance-uksouth.openai.azure.com/'
    )

conversation_sum = ConversationChain(
llm=model,
memory=ConversationSummaryMemory(llm=model)

    )
def convo_chain(chain, query):
    with get_openai_callback() as cb:
        result = chain.run(query)
        print(f'Spent a total of {cb.total_tokens} tokens')
    return result


@app.message("Conversation ID #")
def message_hello(message, say):
    new_question = message['text']
    question_text = new_question[26:]
    conversation_id = int(new_question[17:][:9])
    say ({"text": 'Thanks for your message! I will go and retreive an answer',
          "thread_ts": nested_dict[conversation_id]['conversation_thread_id']})

    ai_answer = convo_chain(
        nested_dict[conversation_id]['conversation_history'],
        question_text
    )
    print (conversation_sum)
    say ({"text": ai_answer,
          "thread_ts": nested_dict[conversation_id]['conversation_thread_id']}) 
    nested_dict[conversation_id]['conversation_history'] = conversation_sum
    conversation_sum.memory.clear()
    say(
            {"thread_ts": nested_dict[conversation_id]['conversation_thread_id'],
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

@app.event("message")
def handle_message_events(body, logger):
    logger.info

@app.event("app_mention")
def kick_off_event(event, say):
    print (event)
    message_text = event["text"]
    thread_id = event.get("ts")
    convo_id = (random.randint(100000000, 999999999))
    say ({"text": 'Hi there! Your conversation ID is ' + str(convo_id),
          "thread_ts": thread_id})
    awaiting_text = "Thank you for your query. I will now go and retrieve your answer, this can take up to 3 minutes to complete. If your answer is not provided in this time, please raise a support request using the following link: https://www.servicenow.com/uk/"
    say ({"text": awaiting_text,
          "thread_ts": thread_id})

    # Call to openAI. Will need to be updated once the deployed model is available, as it currently facing a generic openAI conversation
    # TODO: Add in ConversationChain library to maintain context/ask further Qs. Will need an if else loop looking at the thread_id, again will need to extract thread_id somehow, may add in buttons to continue the conversation, then to go to feedback.
    ai_answer = convo_chain(
        conversation_sum,
        message_text
    )
    # Update to dicts to add conversation history, thread_ID to post into, and the date when the conversation was last updated

    nested_dict[convo_id] = {
            'conversation_history': conversation_sum,
            'conversation_thread_id': thread_id,
            'conversation_last_updated_date': date.today()
        }
    answer_text = f"Hi there! This is the OpenAI answer I found in response to your question:\n\n {ai_answer} \n\n I am however just a bot. If your question was not answered satisfactorily, please select the relevant box."
    conversation_sum.memory.clear()
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
                                'action_id': 'resolved_button'
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "This has not resolved my query"},
                                "value": "no",
                                'action_id': 'unresolved_button'
                            },
                        ],
                    },
                ]
            }, 
            
        )


# Handle button clicks

@app.action("unresolved_button")
def handle_negative_action(ack, body, client, logger, say):
    ack()
    thread_id = (body['container']['thread_ts'])
    say ({"text": "Sorry to hear your answer was not resolved. If you wish to ask any further questions, please do so in this thread. Please start all conversations with 'Conversation ID #xxx'. Otherwise I cannot pick up the message. Context from previous questions will be maintained, so for an example you could ask 'Conversation ID #123, name three UK bird species'.",
          "thread_ts": thread_id})
    
    say ({'text' : "Otherwise, if your question is still not answered, you can raise a support request here:",
          "thread_ts": thread_id})

        # Ask for feedback
    # client.views_open(
    #     trigger_id = body['trigger_id'],
 
    #     view={
    #         "type": "modal",
    #         "callback_id": "external_modal",
    #         "title": {
    #             "type": "plain_text",
    #             "text": "Raise a support ticket"
    #         },
    #         "blocks": [
    #             {
    #                 "type": "section",
    #                 "text": {
    #                     "type": "mrkdwn",
    #                     "text": f"Please follow this link to raise a support ticket for your issue: {url}"
    #                 },
    #                 "accessory": {
    #                     "type": "button",
    #                     "text": {
    #                         "type": "plain_text",
    #                         "text": "Raise a support ticket",
    #                     },
    #                     "url": url
    #                 }
    #             }
    #         ]
    #     }
    # )
    logger.info(body)    

@app.action("resolved_button")
def handle_positive_action(ack, body, say, logger):
    ack()
    thread_id = (body['container']['thread_ts'])
    text = 'Thank you for using the powerful app service! If you have any further feedback on this service, please leave it as a reply to this thread. Our team will review all feedback to improve the service.'
    say({"thread_ts": thread_id, 'text': text})
    logger.info(body)    

if __name__ == "__main__":
    SocketModeHandler(app, powerfulappappsecret).start()