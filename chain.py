from langchain.schema import StrOutputParser
from prompts import prompt
from langchain.chains import LLMChain

def build_chain(llm):
    # chain = LLMChain(llm = llm , prompt = prompt , memory = memory, verbose=False) | StrOutputParser()
    # chain = prompt | llm | StrOutputParser() | memory
    return prompt | llm | StrOutputParser()
    # return chain
