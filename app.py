from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain_openai import AzureChatOpenAI
from langchain.memory import ChatMessageHistory
import random
import os
from datetime import date
from typing import TypedDict

# Grab the API keys
bot_token = os.environ["SLACK_BOT_TOKEN"]
app_token = os.environ["SLACK_APP_TOKEN"]

# Set up the dict we will store the records in
nested_dict = {}

app = App(token=bot_token)

class Item (TypedDict):
    type: str
class Event (TypedDict):
    type : str
    user : str
    item : Item

# Model needs to be updated once the endpoint is deployed with training data
model = AzureChatOpenAI(
    openai_api_version="2023-08-01-preview",
    azure_deployment="eps-assistant-model",
    azure_endpoint="https://openapi-platforms-epsassist-poc-instance-uksouth.openai.azure.com/",
)


# When a user @ mentions the app. The start to add a new question/record to the dict.
@app.event("app_mention")
def kick_off_event(event, say):
    # Extract the actual question
    message_text = event["text"]
    index_of_space = message_text.find(" ")
    message_text = message_text[index_of_space + 1 :]
    print(message_text)
    # Extract the thread_id so that we can keep the context of the query.
    thread_id = event.get("ts")
    # Assign a conversation ID. Do a little while loop to generate a new number if the ID already exists.
    convo_id = random.randint(100000000, 999999999)
    while convo_id in nested_dict:
        convo_id = random.randint(100000000, 999999999)
    # Tell them the conversation ID
    convo_id_text = f"Hi there! Your conversation ID is {convo_id}"
    say({"text": convo_id_text, "thread_ts": thread_id})
    # Say we're going to grab the answer. This time can be extended as needed, also need to add in how we want to handle failed calls.
    awaiting_text = "Thank you for your query. I will now go and retrieve your answer, this can take up to 3 minutes to complete. If your answer is not provided in this time, please raise a support request using the following link: https://www.servicenow.com/uk/"
    say({"text": awaiting_text, "thread_ts": thread_id})

    # Create the conversation history
    history = ChatMessageHistory()
    history.add_user_message(message_text)
    ai_answer = model(history.messages).content
    history.add_ai_message(ai_answer)

    # Update to dicts to add conversation history, thread_ID to post into, and the date when the conversation was last updated
    nested_dict[convo_id] = {
        "conversation_history": history,
        "conversation_thread_id": thread_id,
        "conversation_last_updated_date": date.today(),
    }
    # Push the answer back to the user.
    answer_text = f"Hi there! This is the OpenAI answer I found in response to your question:\n\n {ai_answer} \n\n I am however just a bot. If your question was not answered satisfactorily, please select the relevant box."
    say({"text": answer_text, "thread_ts": thread_id})
    # Send a message with buttons asking for feedback
    say(
        {
            "thread_ts": thread_id,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "markdwn",
                        "text": "Please select an option for how satisfied you are with the provided answer:",
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "This has resolved my query",
                            },
                            "value": "yes",
                            "action_id": "resolved_button",
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "This has not resolved my query",
                            },
                            "value": "no",
                            "action_id": "unresolved_button",
                        },
                    ],
                },
            ],
        },
    )


# Handle button clicks


@app.message("Conversation ID #")
def message_hello(message, client, say):
    new_question = message["text"]
    username = message["user"]
    username = client.users_info(user=username)
    username = username["user"]["name"]
    question_text = new_question[26:]
    # Extract the conversation id to be passed to the dict.
    conversation_id = int(new_question[17:][:9])
    kick_off_message = f"Thanks for your message! I will go and retreive an answer"
    say(
        {
            "text": kick_off_message,
            "thread_ts": nested_dict[conversation_id]["conversation_thread_id"],
        }
    )
    history = ChatMessageHistory()
    # Add history of the conversation we want to work with.
    history.add_ai_message(str(nested_dict[conversation_id]["conversation_history"]))
    history.add_user_message(question_text)
    ai_answer = model(history.messages).content
    # if user asks a question outside the thread, send a message to the thread with the username asking and the question. Maintains context.
    if message.get("ts") != nested_dict[conversation_id]["conversation_thread_id"]:
        user_identification = f"User {username} asked {question_text}"
        say(
            {
                "text": user_identification,
                "thread_ts": nested_dict[conversation_id]["conversation_thread_id"],
            }
        )
    say(
        {
            "text": ai_answer,
            "thread_ts": nested_dict[conversation_id]["conversation_thread_id"],
        }
    )

    # Update dict for latest history, and the most recent updated date.
    nested_dict[conversation_id]["conversation_history"] = history
    nested_dict[conversation_id]["conversation_last_updated_date"] = date.today()

    say(
        {
            "thread_ts": nested_dict[conversation_id]["conversation_thread_id"],
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
                            "text": {
                                "type": "plain_text",
                                "text": "This has resolved my query",
                            },
                            "value": "yes",
                            "action_id": "resolved_button",
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "This has not resolved my query",
                            },
                            "value": "no",
                            "action_id": "unresolved_button",
                        },
                    ],
                },
            ],
        },
    )


@app.action("unresolved_button")
def handle_negative_action(ack, body, logger, say):
    ack()
    thread_id = body["container"]["thread_ts"]
    say(
        {
            "text": "Sorry to hear your answer was not resolved. If you wish to ask any further questions, please do so in this thread. Please start all conversations with 'Conversation ID #xxx'. Otherwise I cannot pick up the message. Context from previous questions will be maintained, so for an example you could ask 'Conversation ID #123, name three UK bird species'.",
            "thread_ts": thread_id,
        }
    )

    say(
        {
            "text": "Otherwise, if your question is still not answered, you can raise a support request here:",
            "thread_ts": thread_id,
        }
    )

    # Leaving these in in case we want them. Opens a new dialogue box which gives a URL to open, in case this is needed.
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
    thread_id = body["container"]["thread_ts"]
    text = "Thank you for using the powerful app service! If you have any further feedback on this service, please leave it as a reply to this thread. Our team will review all feedback to improve the service."
    say({"thread_ts": thread_id, "text": text})
    logger.info(body)


if __name__ == "__main__":
    SocketModeHandler(app, app_token).start()
