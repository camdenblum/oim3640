from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

response = client.responses.create(
    model="gpt-5-nano", 
    input="Give me a prompt that I can use for Claude Code to make an agentic stock trading bot that uses yfinance to get stock data and make trades based on that data. Have it be able to manage a brokerage account and execute trades, and also be able to learn from its successes and failures to improve its trading strategy over time. Make the prompt as detailed as possible so that Claude Code can create a really good bot."
)
print(response.output_text)