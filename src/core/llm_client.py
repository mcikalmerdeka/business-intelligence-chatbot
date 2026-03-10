"""LLM client for generating responses"""

import streamlit as st
from typing import Optional, List, Dict
from openai import OpenAI
from anthropic import Anthropic
from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, MODEL_OPTIONS, logger_llm

logger = logger_llm


class LLMClient:
    """Handle interactions with language models"""
    
    def __init__(self, model_choice: str):
        """
        Initialize LLM client
        
        Args:
            model_choice: Name of the model to use
        """
        self.model_choice = model_choice
        self.client = self._initialize_client()
    
    def _is_openai_model(self) -> bool:
        model_id = MODEL_OPTIONS.get(self.model_choice, self.model_choice)
        return model_id.startswith("gpt-") or model_id.startswith("o1") or model_id.startswith("o3")

    def _initialize_client(self):
        logger.info(f"Initializing LLM client for model: {self.model_choice}")
        if self._is_openai_model():
            return OpenAI(api_key=OPENAI_API_KEY)
        return Anthropic(api_key=ANTHROPIC_API_KEY)

    def generate_response(
        self,
        question: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        try:
            logger.info(f"Generating response with model: {self.model_choice}")
            model_id = MODEL_OPTIONS.get(self.model_choice, self.model_choice)
            if self._is_openai_model():
                return self._generate_openai_response(question, system_prompt, model_id, history)
            return self._generate_anthropic_response(question, system_prompt, history)
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            st.error(f"Error with model API: {e}")
            return None
    
    def _generate_openai_response(
        self, 
        question: str, 
        system_prompt: str, 
        model_name: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate response using OpenAI API"""
        logger.debug(f"Calling OpenAI API with model: {model_name}")
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": question})
        
        response = self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=4000
        )
        logger.info(f"OpenAI response received, tokens used: {response.usage.total_tokens if response.usage else 'unknown'}")
        return response.choices[0].message.content
    
    def _generate_anthropic_response(
        self, 
        question: str, 
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate response using Anthropic API"""
        # Determine the model name
        model_name = MODEL_OPTIONS.get(self.model_choice, self.model_choice)
        logger.debug(f"Calling Anthropic API with model: {model_name}")
        
        messages = []
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": question})
        
        response = self.client.messages.create(
            model=model_name,
            system=system_prompt,
            messages=messages,
            max_tokens=4000
        )
        logger.info(f"Anthropic response received, tokens used: {response.usage.input_tokens + response.usage.output_tokens if response.usage else 'unknown'}")
        return response.content[0].text
