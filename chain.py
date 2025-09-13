from langchain.schema import StrOutputParser
from prompts import prompt
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import LLMChain

memory = ConversationBufferWindowMemory(memory_key="chat_history", input_key="query", return_messages=True , k = 3)


def build_chain(llm):
    return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)

# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_community.chat_models import ChatOpenAI
# from langchain.memory import ConversationBufferMemory
# from langchain_core.runnables import RunnablePassthrough

# # Initialize LLM and memory
# llm = ChatOpenAI(temperature=0)
# memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# # Create a prompt template with MessagesPlaceholder for chat history
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are a helpful AI assistant."),
#     MessagesPlaceholder(variable_name="chat_history"),
#     ("human", "{question}")
# ])

# # Define the chain using LCEL and RunnablePassthrough for memory
# chain = (
#     RunnablePassthrough.assign(
#         chat_history=lambda x: memory.load_memory_variables({})["chat_history"]
#     )
#     | prompt
#     | llm
# )

# # Invoke the chain and update memory
# input_data = {"question": "What is the capital of France?"}
# response = chain.invoke(input_data)
# memory.save_context(input_data, {"output": response.content})
# print(response.content)

# # Invoke again with updated memory
# input_data_2 = {"question": "And what about Germany?"}
# response_2 = chain.invoke(input_data_2)
# memory.save_context(input_data_2, {"output": response_2.content})
# print(response_2.content)