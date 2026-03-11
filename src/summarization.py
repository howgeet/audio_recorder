"""Meeting summarization module using LLM."""

import time
from typing import Dict, Any
from openai import OpenAI

from src.config import config

class MeetingSummarizer:
    """Handles meeting summarization using LLM."""
    
    def __init__(self):
        """Initialize the summarizer."""
        if not config.openai_api_key:
            raise ValueError("OpenAI API key is not configured.")
        
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.llm_model
        self.temperature = config.temperature
    
    def generate_summary(self, transcript: str, language: str = "en") -> Dict[str, str]:
        """Generate a comprehensive meeting summary.
        
        Args:
            transcript: Full meeting transcript
            language: Language of the meeting (for context)
            
        Returns:
            Dictionary containing different summary sections
        """
        print(f"\n📝 Generating meeting summary...")
        print(f"   Model: {self.model}")
        
        try:
            start_time = time.time()
            
            # Determine language for prompt
            is_turkish = language and language.lower() in ['tr', 'turkish']
            
            # Create comprehensive prompt
            prompt = self._create_summary_prompt(transcript, is_turkish)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert meeting analyst who creates comprehensive, well-structured meeting summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=2000
            )
            
            summary_text = response.choices[0].message.content
            
            elapsed_time = time.time() - start_time
            print(f"✅ Summary generated in {elapsed_time:.2f} seconds")
            
            return {
                'full_summary': summary_text,
                'language': language,
                'model': self.model
            }
            
        except Exception as e:
            print(f"❌ Summarization error: {e}")
            raise
    
    def _create_summary_prompt(self, transcript: str, is_turkish: bool = False) -> str:
        """Create a detailed prompt for summarization.
        
        Args:
            transcript: Meeting transcript
            is_turkish: Whether the meeting is in Turkish
            
        Returns:
            Formatted prompt string
        """
        if is_turkish:
            prompt = f"""
Aşağıdaki toplantı transkriptini analiz edin ve kapsamlı bir özet oluşturun.

Özet aşağıdaki bölümleri içermelidir:

1. **GENEL ÖZET** (2-3 cümle)
   - Toplantının ana konusu ve amacı

2. **ANA KONU BAŞLIKLARI**
   - Tartışılan tüm önemli konuları listeleyin
   - Her konu için kısa açıklama

3. **ÖNEMLİ KARARLAR**
   - Alınan kararları listeleyin
   - Kim tarafından alındı (biliyorsak)

4. **EYLEM MADDELERI**
   - Yapılması gereken görevler
   - Sorumlular (önemli ise)
   - Süreler (bahsedildiyse)

5. **SONUÇLAR VE SONRAKI ADIMLAR**
   - Toplantının genel sonuçları
   - Gelecek toplantılar veya takip edilecekler

TRANSKRIPT:
{transcript}
"""
        else:
            prompt = f"""
Analyze the following meeting transcript and create a comprehensive summary.

The summary should include the following sections:

1. **EXECUTIVE SUMMARY** (2-3 sentences)
   - Main topic and purpose of the meeting

2. **KEY DISCUSSION POINTS**
   - List all important topics discussed
   - Brief explanation for each topic

3. **DECISIONS MADE**
   - List all decisions made during the meeting
   - Who made them (if known)

4. **ACTION ITEMS**
   - Tasks that need to be completed
   - Responsible parties (if mentioned)
   - Deadlines (if mentioned)

5. **CONCLUSIONS AND NEXT STEPS**
   - Overall outcomes of the meeting
   - Future meetings or follow-ups

TRANSCRIPT:
{transcript}
"""
        
        return prompt
    
    def format_summary(self, summary_result: Dict[str, str]) -> str:
        """Format summary for output.
        
        Args:
            summary_result: Summary result dictionary
            
        Returns:
            Formatted summary string
        """
        output = []
        output.append("=" * 80)
        output.append("MEETING SUMMARY")
        output.append("=" * 80)
        output.append("")
        output.append(f"Generated with: {summary_result.get('model', 'N/A')}")
        if summary_result.get('language'):
            output.append(f"Meeting Language: {summary_result['language'].upper()}")
        output.append("")
        output.append("-" * 80)
        output.append("")
        output.append(summary_result.get('full_summary', 'No summary available'))
        output.append("")
        output.append("-" * 80)
        output.append("=" * 80)
        
        return "\n".join(output)
