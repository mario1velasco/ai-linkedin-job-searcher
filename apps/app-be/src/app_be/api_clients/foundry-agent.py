# Before running the sample:
#    pip install azure-ai-projects>=2.1.0
# ? Install azure cli https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/install-cli-sdk?tabs=linux&pivots=programming-language-python#install-the-azure-cli-and-sign-in


from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

endpoint = "https://ai-project-mario-v-resource.services.ai.azure.com/api/projects/ai-project-mario-v"

# ! With azure cli this is automaticaly: credential=DefaultAzureCredential(),
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

# !We select the agent that we have created in Foundry
my_agent = "DeepSeek-V4-Flash-Agent"
my_version = "1"

openai_client = project_client.get_openai_client()

# Reference the agent to get a response
response = openai_client.responses.create(
    input=[{"role": "user", "content": "Tell me what you can help with."}],
    extra_body={
        "agent_reference": {
            "name": my_agent,
            "version": my_version,
            "type": "agent_reference",
        }
    },
)

print(f"Response output: {response.output_text}")
