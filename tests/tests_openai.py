from openai import OpenAI
from os import getenv
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=getenv("OPENAI_KEY")
)

response = client.responses.create(
    model="gpt-5.2",
    input="Write a one-sentence bedtime story about a unicorn."
)

print(response.output_text)
