
from client import llm
from chain import build_chain
from data_loader import load_excel, dataframe_to_text


df = load_excel("Lido Mall AI.xlsx", sheet_name="Main Data")
context = dataframe_to_text(df, max_rows=None)
chain = build_chain(llm)

def run_query(query: str) -> str:
	"""Run a user query through the chatbot chain and return the response."""
	response = chain.invoke({"context": context, "query": query})
	return str(response)


if __name__ == "__main__":
	query = "suggest me nice places for family dinner"
	print(run_query(query))

