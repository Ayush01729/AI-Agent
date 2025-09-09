from langchain.schema import StrOutputParser
from prompts import prompt
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import LLMChain

memory = ConversationBufferWindowMemory(memory_key="chat_history", input_key="query", return_messages=True , k = 3)


def build_chain(llm):
    return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)

