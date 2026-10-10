Python Version: src/digest.py + src/prompts.py

LangChain Version: src/digest_langchain.py

1. With LangChain, two prompts run in parallel, while in the pure Python version, two prompts run in sequential order.
2. With LangChain, switching to a different provider only changes one line (`ChatOpenAI(...)`), while the raw version needs a different SDK, client and client method. Switching models within the same provider is a config change in both versions.
3. LangChain brings in many more dependencies. For a simple prompt it is overkill.
4. LangChain enables sharing the variables for multiple prompts, while the raw version needs to pass them separately.
5. The raw version shows how the API is called and the full response, while LangChain wraps the details and only exposes the formatted response. Sometimes it is difficult to debug.
6. The raw version sends the instructions and the article separately (`instructions=...` and `input=article`), while my LangChain version puts the article inside the prompt template, so both go to the model as one message. The chain line `template | llm | parser` does not show this difference.