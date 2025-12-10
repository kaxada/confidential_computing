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
        for res in valid_responses:
            site_id = res.get('site_id', 'Unknown')
            resp_text = res.get('response', '')
            context += f"--- Report from {site_id} ---\n{resp_text}\n\n"

        client = self._get_client()
        if not client:
            return f"**Aggregated Results (Raw):**\n\n{context}"

        prompt = f"""
        You are the Central Hub AI. The user asked: "{user_query}" 
        
        Synthesize the following reports from our distributed research labs:
        {context}
        
        Provide a unified, coherent answer. Highlight consensus or contradictions between sites.
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

aggregator = ResultAggregator()
