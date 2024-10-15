from os import environ
from tavily import TavilyClient

class Search:
    def __init__(self):
        self.token = environ['SEARCH-TOKEN']

    def search(self, query):
        tavily_client = TavilyClient(api_key=self.token)
        response = tavily_client.qna_search(query)
        return str(response)
if __name__ == "__main__":
    search = Search()
    search.search("python")
