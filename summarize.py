from openai import OpenAI
from ipydex import IPS

# Example: if Cortex is running on localhost, port 39281
client = OpenAI(
    base_url="http://localhost:8123/v1",
    api_key="not-needed"  # Authentication is not required for local deployment
)


with open("out.txt") as fp:
    input_lines = fp.readlines()


# experiences the connection to the cortex server is lost after about 8 requests (or maybe because the prompt is too big)


dl = 50
previous_summaries = []

context = ""

for part_num in range(0, len(input_lines), dl):
    idx_start = part_num
    idx_end = min(idx_start + dl, len(input_lines))
    current_part = "\n".join(input_lines[idx_start:idx_end])

    # Build prompt with previous summaries context
    if previous_summaries:
        context = "Previous summaries:\n" + "\n".join(previous_summaries) + "\n\n"
        prompt = (
            f"{context}Please briefly summarize new and important information from the following "
            f"partial transcript of a german podcast in a list "
            f"of markdown bullet points (`- ...`). Do not give an intro nor an outro: Transcript:\n"
            f"\n{current_part}"
        )
    else:
        prompt = (
            f"Please briefly summarize the following partial transcript of a german podcast in a list "
            f"of markdown bullet points (`- ...`). Do not give an intro nor an outro."
            f"\nTranscript:\n\n{current_part}"
        )

    print("len=", len(context) + len(prompt))
    response = client.chat.completions.create(
        model="gemma3:27b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        # tools=tools,
        seed = 1900,
    )

    summary = response.choices[0].message.content.replace("<end_of_turn>", "").strip()
    previous_summaries.append(summary)

    # Store result in text file
    part_index = part_num // dl
    filename = f"summary_part_{part_index:03d}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(previous_summaries))

    print(f"Part {part_index} summarized and saved to {filename}")

IPS()
