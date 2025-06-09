from openai import OpenAI
from ipydex import IPS

# Example: if Cortex is running on localhost, port 39281
client = OpenAI(
    base_url="http://localhost:8123/v1",
    api_key="not-needed"  # Authentication is not required for local deployment
)


with open("out.txt") as fp:
    input_lines = fp.readlines()


dl = 100
idx_start = 0
part1 = "\n".join(input_lines[idx_start : idx_start + dl])

response = client.chat.completions.create(
    model="gemma3:27b",
    messages=[
        {"role": "user", "content": f"Please summarize the following partial transcript of a german podcast:\n{part1}"}
    ],
    # tools=tools,
    seed = 1900,
)

print(response.choices[0].message.content)

IPS()
