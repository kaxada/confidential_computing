from openai import OpenAI
from app.core.config import settings
import logging

class ResultAggregator:
    def __init__(self):
        self.client = None
    
    def _get_client(self):
        if not self.client and settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
        return self.client

    def synthesize_results(self, user_query: str, site_results: list) -> str:
        """
        Aggregates results from Site 1, Site 2, etc. into one insight.
        """
        valid_responses = [r for r in site_results if r and r.get('status') == 'success']
        
        if not valid_responses:
            return "Unable to retrieve insights from any research site. Please try again later."

        context = ""
        for i, res in enumerate(valid_responses):
            site_id = res.get('site_id', 'Unknown')
            resp_text = res.get('response', '')
            context += f"--- Report from Source {i+1} ({site_id}) ---\n{resp_text}\n\n"

        client = self._get_client()
        if not client:
            return f"**Aggregated Results (Raw):**\n\n{context}"

        prompt = f"""
        You are the Central Hub AI. The user asked: "{user_query}" 
        
        Synthesize the following reports from our distributed research labs:
        {context}
        
        Instructions:
        1. Provide a unified, coherent answer.
        2. Highlight consensus or contradictions between sources.
        3. DO NOT explicitly mention "Site 1", "Site 2", "Site 3", or "Source X" in your final response. 
           Instead, refer to them as "the research data", "hospital records", "lab results", or "available reports".
           Make the response sound natural and seamless.
        """

        try:
            response = client.chat.completions.create(
                model=settings.aggregation_model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Aggregation error: {e}")
            return f"Error synthesizing results. Raw data:\n\n{context}"

    def generate_title(self, user_query: str, assistant_response: str) -> str:
        """
        Generates a short title (3-5 words) based on the conversation start.
        """
        client = self._get_client()
        if not client:
            return "New Chat"
            
        prompt = f"""
        Generate a very short, concise title (max 5 words) for a conversation that starts with:
        User: "{user_query}"
        Assistant: "{assistant_response[:500]}..."
        
        Do not use quotes. Just the title.
        """
        
        try:
            response = client.chat.completions.create(
                model=settings.aggregation_model,
                messages=[{"role": "user", "content": prompt}]
            )
            title = response.choices[0].message.content.strip().replace('"', '')
            return title
        except Exception as e:
            logging.error(f"Title generation error: {e}")
            return "New Chat"

aggregator = ResultAggregator()
