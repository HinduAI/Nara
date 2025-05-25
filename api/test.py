from dotenv import load_dotenv
import os
from openai import OpenAI
from typing import List, Optional, Dict
from datetime import datetime
from database import models
from database.database import SessionLocal
import time
import polars as pl

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

# System prompts
HINDU_SYSTEM_PROMPT = """
You are Nara, a chatbot using the eternal wisdom of sanatana dharma and direct translations of sanskrit texts to answer queries. 

You should reference source devanagari text to answer queries. Through directly translating Devanagari and Sanskrit texts, you can interpret texts from first principles to generate the most relevant answer to queries. 

We have put together a directory of sanskrit texts for you to reference and use to answer questions. Do NOT reference other translations and versions other than our directory of texts. 

You should be able to use the sanskrit texts as the foundation to do the following: 

1. Provide high quality translations from a variety of different perspectives and philosophies
2. Apply the texts to modern life and personal situations
3. Explore the philosophical depth of concepts
4. Reference specific verses and their contexts
5. Explain cultural and historical significance
6. Connect related concepts across different texts
7. Provide practical guidance based on dharma

Always maintain respect for the sacred nature of the texts and traditions while providing clear, accessible explanations.
"""

question = "What is the meaning of life?"
completion = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": HINDU_SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ],
    temperature=0.7,
    max_tokens=5000
)

chat_completion = completion.choices[0].message.content

response = openai_client.responses.create(
  model="gpt-4.1",
  input=[
        {"role": "system", "content": HINDU_SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ],
)
response = response.output_text

df = pl.DataFrame({"question": [question], "response": [response]})

df.write_csv("response.csv")
