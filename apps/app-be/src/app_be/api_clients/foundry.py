from openai import OpenAI

from app_be.config import FOUNDRY_API_KEY

endpoint = "https://ai-project-mario-v-resource.services.ai.azure.com/openai/v1"
deployment_name = "DeepSeek-V4-Flash"

client = OpenAI(base_url=endpoint, api_key=FOUNDRY_API_KEY)

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {
            "role": "user",
            "content": "What is the province of Simancas",
        }
    ],
)

print(completion.choices[0].message)
