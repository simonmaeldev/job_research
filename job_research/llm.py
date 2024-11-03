"""
LLM Interface Module

This module provides a unified interface for interacting with various Language Models (LLMs) including:
- Anthropic's Claude models (opus, sonnet, haiku)
- OpenAI's GPT models (3.5 and 4)
- Local Ollama models

It handles:
- Model selection and API calls
- Token counting and cost calculation
- Error handling and retries
- Response parsing and formatting
"""

import os
import openai
import anthropic
from anthropic import Anthropic
import re
import ollama
import time

# Model configuration constants
MODEL_NAMES = {
    "opus": "claude-3-opus-20240229",
    "sonnet": "claude-3-5-sonnet-20240620",
    "haiku": "claude-3-haiku-20240307",
    "gpt3.5": "gpt-3.5-turbo",
    "gpt4": "gpt-4-turbo-preview",
    "llama3:8b": "llama3:8b",
    "llama3:instruct": "llama3:instruct",
    "gpt-4o-mini": "gpt-4o-mini",
}

MODEL_PRICING = {
    "opus": {"input_cost_per_mtok": 15.00, "output_cost_per_mtok": 75.00},
    "sonnet": {"input_cost_per_mtok": 3.00, "output_cost_per_mtok": 15.00},
    "haiku": {"input_cost_per_mtok": 0.25, "output_cost_per_mtok": 1.25},
    "gpt3.5": {"input_cost_per_mtok": 0.5, "output_cost_per_mtok": 1.5},
    "gpt4": {"input_cost_per_mtok": 10.00, "output_cost_per_mtok": 30.0},
    "llama3:8b": {"input_cost_per_mtok": 0.0, "output_cost_per_mtok": 0.0},
    "llama3:instruct": {"input_cost_per_mtok": 0.0, "output_cost_per_mtok": 0.0},
    "gpt-4o-mini": {"input_cost_per_mtok": 0.15, "output_cost_per_mtok": 0.6},
}

def _query_claude(query: str, model_name: str, api_key: str = None) -> dict:
    """Handle Claude API calls with retry logic for server overload"""
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
            return {
                "response": response.content[0].text,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cost": calculate_subagent_cost(model_name, 
                                              response.usage.input_tokens, 
                                              response.usage.output_tokens),
            }
        except anthropic.InternalServerError as e:
            error_details = e.response.json()
            error_code = error_details.get('error', {}).get('type', 'unknown_error')
            
            if error_code == 'overloaded_error':
                print(f"Error 529 - Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            raise
    raise Exception("All retry attempts failed")

def _query_openai(query: str, model_name: str, api_key: str = None) -> dict:
    """Handle OpenAI API calls"""
    openai.api_key = api_key or os.environ["OPENAI_API_KEY"]
    response = openai.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": query}],
    )
    return {
        "response": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "cost": calculate_subagent_cost(model_name, 
                                      response.usage.prompt_tokens, 
                                      response.usage.completion_tokens),
    }

def _query_ollama(query: str, model_name: str) -> dict:
    """Handle local Ollama model calls"""
    response = ollama.generate(model=model_name, prompt=query)
    return {
        "response": response["response"],
        "cost": 0
    }

def query_llm(query: str, model: str = "gpt-4o-mini", api_key: str = None) -> dict:
    """
    Query an LLM with automatic model selection and error handling.

    Args:
        query: The prompt/question to send to the LLM
        model: Model identifier from MODEL_NAMES
        api_key: Optional API key (defaults to environment variable)

    Returns:
        dict containing:
        - response: The LLM's text response
        - input_tokens: Number of input tokens (if applicable)
        - output_tokens: Number of output tokens (if applicable)
        - cost: Calculated cost in USD
    """
    if model not in MODEL_NAMES:
        raise ValueError(f"Unsupported model: {model}")

    model_name = MODEL_NAMES[model]

    if "claude" in model_name:
        return _query_claude(query, model_name, api_key)
    elif "gpt" in model_name:
        return _query_openai(query, model_name, api_key)
    else:
        return _query_ollama(query, model_name)

def calculate_subagent_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate API call cost based on token usage and model pricing.
    
    Args:
        model: Model identifier from MODEL_PRICING
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
    
    Returns:
        Total cost in USD
    """
    input_cost = (input_tokens / 1_000_000) * MODEL_PRICING[model]["input_cost_per_mtok"]
    output_cost = (output_tokens / 1_000_000) * MODEL_PRICING[model]["output_cost_per_mtok"]
    return input_cost + output_cost

def search_for_tag(answer: dict, tag: str) -> str:
    """
    Extract content between XML-style tags from LLM response.
    
    Args:
        answer: Dict containing LLM response
        tag: Tag name to search for (without < >)
    
    Returns:
        Content between tags or None if not found
    """
    regex = f'<{tag}>(.*?)</{tag}>'
    match = re.search(regex, answer["response"], re.DOTALL)
    if match:
        return match.group(1)
    print(f"============= ALERT : no tag {tag} found. Return None. Text:\n{answer["response"]}")
    return None

def prompt_formatter(prompt_to_format: str) -> str:
    """
    Format a prompt using a metaprompt template and get LLM response.
    
    Args:
        prompt_to_format: Raw prompt to be formatted
    
    Returns:
        Formatted LLM response
    """
    metaprompt_path = '/home/mael/Documents/agentic_projetcs/projets_perso/aait/aait/metaprompt.txt'
    with open(metaprompt_path, 'r') as f:
        metaprompt = f.read()
        full_query = metaprompt.replace('{{prompt}}', prompt_to_format)
        result = query_llm(full_query, model="sonnet")
        return result['response']

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
