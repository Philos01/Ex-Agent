from ollama import chat

response = chat(
  model='qwen3:4b-instruct',
  messages=[{'role': 'user', 'content': 'How many letter r are in strawberry?'}],
  think=True,
  stream=False,
)

print('Thinking:\n', response.message)
print('Answer:\n', response.message.content)