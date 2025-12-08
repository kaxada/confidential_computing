# aggregator.py
from openai import OpenAI
import config_hub

class ResultAggregator:
    def __init__(self):
        self.client = OpenAI(api_key=config_hub.OPENAI_API_KEY)

    def synthesize_results(self, user_query: str, site_results: list) -> str:
        """
        Aggregates results from Site 1, Site 2, etc. into one insight.
        """
        valid_responses = [r for r in site_results if r['status'] == 'success']
        
        if not valid_responses:
            return "Unable to retrieve insights from any research site."

        # Compile site reports
        context = ""
        for res in valid_responses:
            site_id = res['site_id']
            # We treat site answers as secure, scrubbed inputs
            context += f"--- Report from {site_id} ---\n{res['response']}\n\n"

        # Hub LLM Prompt
        prompt = f"""
        You are the Central Hub AI. The user asked: "{user_query}"
        
        Synthesize the following reports from our distributed research labs:
        {context}
        
        Provide a unified answer. Highlight consensus or contradictions between sites.
        """

        response = self.client.chat.completions.create(
            model=config_hub.AGGREGATION_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content