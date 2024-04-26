import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

keyVaultName = os.environ["KEY_VAULT_NAME"]
bot_token = os.environ["SLACK_BOT_TOKEN"]
app_token = os.environ["SLACK_APP_TOKEN"]
KVUri = f"https://{keyVaultName}.vault.azure.net"

credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)

secretNameapp = input("powerfulappappsecret")
secretNamebot = input("powerfulappbotsecret")
secretValueapp = input("app_token")
secretValuebot = input("bot_token")


print(f"Creating a secret in {keyVaultName} called '{secretNameapp}' with the value '{secretValueapp}' ...")

print(f"Creating a secret in {keyVaultName} called '{secretNamebot}' with the value '{secretValuebot}' ...")


client.set_secret(secretNameapp, secretValueapp)
client.set_secret(secretNamebot, secretValuebot)


print(" done.")


print(f"Retrieving your secret from {keyVaultName}.")

retrieved_secret_app = client.get_secret(secretNameapp)
retrieved_secret_bot = client.get_secret(secretNamebot)


print(f"Your secret is '{retrieved_secret_app.value}'.")
print(f"Your secret is '{retrieved_secret_bot.value}'.")

