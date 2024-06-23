import os
import openai
import anthropic
from anthropic import Anthropic
import re
import ollama
import time

MODEL_NAMES = {
    "opus": "claude-3-opus-20240229",
    "sonnet": "claude-3-5-sonnet-20240620",
    "haiku": "claude-3-haiku-20240307",
    "gpt3.5": "gpt-3.5-turbo",
    "gpt4": "gpt-4-turbo-preview",
    "llama3:8b": "llama3:8b",
    "llama3:instruct": "llama3:instruct",
}

MODEL_PRICING = {
    "opus": {"input_cost_per_mtok": 15.00, "output_cost_per_mtok": 75.00},
    "sonnet": {"input_cost_per_mtok": 3.00, "output_cost_per_mtok": 15.00},
    "haiku": {"input_cost_per_mtok": 0.25, "output_cost_per_mtok": 1.25},
    "gpt3.5": {"input_cost_per_mtok": 0.5, "output_cost_per_mtok": 1.5},
    "gpt4": {"input_cost_per_mtok": 10.00, "output_cost_per_mtok": 30.0},
    "llama3:8b": {"input_cost_per_mtok": 0.0, "output_cost_per_mtok": 0.0},
    "llama3:instruct": {"input_cost_per_mtok": 0.0, "output_cost_per_mtok": 0.0},
}

def query_llm(query: str, model: str = "haiku", api_key: str = None) -> dict:
    """
    Query an LLM (Anthropic or OpenAI) with the given query and model.

    Args:
        query (str): The query to send to the LLM.
        model (str): The LLM model to use (opus, sonnet, haiku, gpt3.5-turbo, or gpt4-turbo).
        api_key (str, optional): The API key for the LLM service. If not provided, it will be read from the environment variable.

    Returns:
        dict: A dictionary containing the response, input tokens, output tokens, and cost.
    """
    
    if model not in MODEL_NAMES:
        raise ValueError(f"Unsupported model: {model}")

    model_name = MODEL_NAMES[model]

    if "claude" in model_name:
        max_retries = 3
        retry_delay = 10
        for _ in range(max_retries):
            try:
                client = Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
                response = client.messages.create(
                    model=model_name,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": query}],
                )
                result = {
                    "response": response.content[0].text,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "cost": calculate_subagent_cost(model, response.usage.input_tokens, response.usage.output_tokens),
                }
                break
            except anthropic.InternalServerError as e:
                print(type(e))
                print(f'error:{e}|')
                # Access the error details from the response attribute
                error_details = e.response.json()
                error_code = error_details.get('error', {}).get('type', 'unknown_error')
                
                # Check if the error is 'overloaded_error'
                if error_code == 'overloaded_error':
                    print("Erreur 529 - Tentative de reconnexion dans {} secondes...".format(retry_delay))
                    time.sleep(retry_delay)
                else:
                    raise
        else:
            print("Toutes les tentatives ont échoué.")
    elif "gpt" in model_name:
        openai.api_key = api_key or os.environ["OPENAI_API_KEY"]
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": query}],
        )
        result = {
            "response": response.choices[0].message.content,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "cost": calculate_subagent_cost(model, response.usage.prompt_tokens, response.usage.completion_tokens),
        }
    else:
        response = ollama.generate(model=model_name, prompt=query)
        result = {
            "response": response["response"],
            "cost": 0
        }
    return result

def calculate_subagent_cost(model, input_tokens, output_tokens):
    """Calculate the cost of a subagent query based on the model and token usage."""

    input_cost = (input_tokens / 1_000_000) * MODEL_PRICING[model]["input_cost_per_mtok"]
    output_cost = (output_tokens / 1_000_000) * MODEL_PRICING[model]["output_cost_per_mtok"]
    total_cost = input_cost + output_cost

    return total_cost

def search_for_tag(answer: dict, tag: str) -> str:
    regex = f'<{tag}>(.*?)</{tag}>'
    match = re.search(regex, answer["response"], re.DOTALL)
    if match:
        return match.group(1)
    return None

def prompt_formatter(prompt_to_format: str) -> str:
    with open('/home/mael/Documents/agentic_projetcs/projets_perso/aait/aait/metaprompt.txt', 'r') as f:
        full_metaprompt = f.read()
        prompt = full_metaprompt
        full_query = prompt.replace('{{prompt}}', prompt_to_format)
        model = "sonnet"

        # Query the LLM using the query_llm function from llm.py
        result = query_llm(full_query, model=model)
        print(result['response'])

PROMPT_TO_FORMAT = """
Given the following user context:
{{user_context}}

Please create querys to find websites in order to search for jobs that match the user's criteria and experience.
Think step by step, and by doing so, follow the following structure : 
1. In what kind of field / domain does the user want to work? use <scratchpad> tags to think out loud about this.
2. What kind of query can allow you to find websites where you can find jobs?
3. Using this informations, provide your response in the following format, between the tags:
<query_list>list of query separated by a comma, each query is in double quote. Example: "query 1", "query 2", "query 3"</query_list>
provide also the domains in wich the user is interested, separated by a comma, inside <domain_of_interest> tags.
"""

if __name__ == "__main__":
    res = prompt_formatter(PROMPT_TO_FORMAT)
    print(res)
