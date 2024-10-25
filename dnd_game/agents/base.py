# agents/base.py
import os
import aiohttp
from typing import get_args, get_origin  # if we need advanced type checking

from typing import Optional, Type, Union, List, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel
from openai import AsyncOpenAI


import requests
import json
from time import sleep
from enum import Enum, auto
from ..config.settings import get_settings

settings = get_settings()
aclient = AsyncOpenAI(api_key=settings.openai_api_key)

class ModelProvider(Enum):
    OPENAI = auto()
    OLLAMA = auto()

class AgentError(Exception):
    """Base exception for agent-related errors"""
    pass

class ConfigurationError(AgentError):
    """Raised when there's a configuration issue"""
    pass

class ModelCallError(AgentError):
    """Raised when there's an error calling the model"""
    pass

@dataclass
class Task:
    """Represents a specific task for an agent to perform"""
    description: str
    prompt_template: str
    expected_output: str
    agent: 'Agent'
    response_model: Optional[Type[BaseModel]] = None

    def format_prompt(self, **kwargs) -> str:
        try:
            return self.prompt_template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required input: {e}")

    def get_required_inputs(self) -> List[str]:
        """Extract required input names from the prompt template."""
        import re
        return re.findall(r'\{(\w+)\}', self.prompt_template)

class ModelCaller:
    """Handles communication with different LLM providers"""
    def __init__(self):
        # Get settings from config/settings.py
        settings = get_settings()
        self.openai_key = settings.openai_api_key
        self.ollama_host = settings.ollama_host

        if not self.openai_key:
            raise ConfigurationError("OPENAI_API_KEY not found in environment variables")


    def parse_model_string(self, model_string: str) -> tuple[ModelProvider, str]:
        """Parse a model string in the format 'provider|model_name'."""
        try:
            provider, model_name = model_string.lower().split('|')
            if provider == 'openai':
                return ModelProvider.OPENAI, model_name
            elif provider == 'ollama':
                return ModelProvider.OLLAMA, model_name
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except ValueError:
            raise ValueError(f"Invalid model string format: {model_string}")

    async def call_model(
        self,
        model_string: str,
        system_prompt: str,
        prompt: str,
        temperature: float = 0.7,
        response_model: Optional[Type[BaseModel]] = None,
        max_retries: int = 3
    ) -> Union[str, BaseModel]:
        """Unified interface to call different model providers."""
        provider, model_name = self.parse_model_string(model_string)

        for attempt in range(max_retries):
            try:
                if provider == ModelProvider.OPENAI:
                    return await self._call_openai(
                        model_name,
                        system_prompt,
                        prompt,
                        temperature,
                        response_model
                    )
                elif provider == ModelProvider.OLLAMA:
                    if response_model:
                        raise ModelCallError(
                            "Structured output using Pydantic models is not supported with Ollama models. "
                            "This feature is only available with OpenAI models."
                        )
                    return await self._call_ollama(
                        model_name,
                        system_prompt,
                        prompt,
                        temperature
                    )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise ModelCallError(f"Failed after {max_retries} attempts: {str(e)}")
                sleep(2 ** attempt)  # Exponential backoff

    async def _call_openai(
        self,
        model: str,
        system_prompt: str,
        prompt: str,
        temperature: float,
        response_model: Optional[Type[BaseModel]] = None
    ) -> Union[str, BaseModel]:
        """Internal method to call OpenAI API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        if response_model:
            # Add format instructions for structured output
            model_schema = response_model.model_json_schema()
            format_instructions = (
                f"Return the response in the following JSON format:\n"
                f"{json.dumps(model_schema, indent=2)}"
            )
            messages.append({"role": "system", "content": format_instructions})

            response = await aclient.chat.completions.create(model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"})

            response_text = response.choices[0].message.content
            return response_model.model_validate_json(response_text)
        else:
            response = await aclient.chat.completions.create(model=model,
            messages=messages,
            temperature=temperature)
            return response.choices[0].message.content

    async def _call_ollama(
        self,
        model: str,
        system_prompt: str,
        prompt: str,
        temperature: float
    ) -> str:
        """Internal method to call Ollama API."""
        headers = {"Content-Type": "application/json"}
        combined_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        data = {
            "model": model,
            "prompt": combined_prompt,
            "temperature": temperature
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ollama_host}/api/generate",
                headers=headers,
                json=data
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get("response")

class Agent:
    """Base class for all agents"""
    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: str,
        temperature: float = 0.7,
        model_caller: Optional[ModelCaller] = None
    ):

        # Use get_settings from config/settings.py
        # settings = get_settings()

        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.model_caller = model_caller or ModelCaller()

    async def execute_task(self, task: Task, **kwargs) -> Union[str, BaseModel]:
        """Execute a task with the provided inputs"""
        # Validate inputs
        required_inputs = task.get_required_inputs()
        missing_inputs = [inp for inp in required_inputs if inp not in kwargs]
        if missing_inputs:
            raise ValueError(f"Missing required inputs: {missing_inputs}")

        # Format the prompt
        formatted_prompt = task.format_prompt(**kwargs)

        # Call the model
        return await self.model_caller.call_model(
            model_string=self.model,
            system_prompt=self.system_prompt,
            prompt=formatted_prompt,
            temperature=self.temperature,
            response_model=task.response_model
        )

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', model='{self.model}')"