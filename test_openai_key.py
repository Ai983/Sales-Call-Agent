import os
from openai import OpenAI

key = os.getenv("OPENAI_API_KEY")

print("Key present:", bool(key))
print("Key prefix:", key[:10] if key else None)

client = OpenAI(api_key=key)

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Reply with exactly: OK"}
        ],
    )
    print("SUCCESS ✅")
    print("Response:", response.choices[0].message.content)

except Exception as e:
    print("FAIL ❌")
    print(type(e).__name__, e)
