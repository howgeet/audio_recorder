"""Meeting summarization module using LLM."""

import logging
import time
from typing import Dict, List, Optional
from openai import OpenAI

from src.config import config


logger = logging.getLogger(__name__)

class MeetingSummarizer:
    """Handles meeting summarization using LLM."""
    
    def __init__(self):
        """Initialize the summarizer."""
        self.client: Optional[OpenAI] = None
        if config.openai_api_key:
            self.client = OpenAI(api_key=config.openai_api_key)

        self.model = config.llm_model
        self.temperature = config.temperature
        self.hf_model = config.hf_summary_model
    
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
        logger.info("Starting summarization. language=%s transcript_chars=%d", language, len(transcript or ""))
        
        start_time = time.time()

        # Determine language for prompt
        is_turkish = language and language.lower() in ['tr', 'turkish']

        # Create comprehensive prompt
        prompt = self._create_summary_prompt(transcript, is_turkish)

        try:
            if not self.client:
                raise ValueError("OpenAI API key is not configured.")

            summary_text = self._generate_with_openai(prompt)
            elapsed_time = time.time() - start_time
            print(f"✅ Summary generated in {elapsed_time:.2f} seconds")
            logger.info("Summarization completed with OpenAI in %.2f seconds", elapsed_time)

            return {
                'full_summary': summary_text,
                'language': language,
                'model': self.model,
                'provider': 'openai'
            }

        except Exception as openai_error:
            logger.exception("OpenAI summarization failed; switching to Hugging Face fallback")
            print(f"⚠️  OpenAI summarization failed: {openai_error}")
            print("🔄 Falling back to Hugging Face transformers summarization...")

            summary_text = self._generate_with_hf(transcript, is_turkish)
            elapsed_time = time.time() - start_time
            print(f"✅ Fallback summary generated in {elapsed_time:.2f} seconds")
            logger.info("Summarization completed with Hugging Face in %.2f seconds", elapsed_time)

            return {
                'full_summary': summary_text,
                'language': language,
                'model': self.hf_model,
                'provider': 'huggingface'
            }

    def _generate_with_openai(self, prompt: str) -> str:
        """Generate summary text using OpenAI chat completion."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert meeting analyst who creates comprehensive, detailed, and long-form meeting summaries. Your goal is to capture as much meaningful information as possible from the transcript — do not truncate sections or give one-line answers. Write in full sentences with thorough explanations for every section."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=self.temperature,
            max_tokens=4000
        )
        return response.choices[0].message.content

    def _generate_with_hf(self, transcript: str, is_turkish: bool) -> str:
        """Generate summary text using local Hugging Face transformers pipeline."""
        try:
            from transformers import pipeline
        except Exception as import_error:
            logger.exception("transformers import failed")
            raise RuntimeError(
                "Hugging Face transformers fallback is unavailable. "
                "Install dependencies: pip install transformers torch"
            ) from import_error

        hf_kwargs = {
            "task": "summarization",
            "model": self.hf_model,
        }
        if config.huggingface_token:
            hf_kwargs["token"] = config.huggingface_token

        summarizer = pipeline(**hf_kwargs)
        chunks = self._chunk_text(transcript, max_chars=config.hf_summary_max_chars)
        if not chunks:
            return "No transcript text available for summarization."

        chunk_summaries: List[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            logger.info("HF summarizing chunk %d/%d (chars=%d)", idx, len(chunks), len(chunk))
            chunk_input = chunk
            if is_turkish:
                chunk_input = f"Toplanti transkriptini ozetle:\n\n{chunk}"

            result = summarizer(
                chunk_input,
                max_length=220,
                min_length=60,
                do_sample=False,
                truncation=True,
            )
            chunk_summaries.append(result[0]["summary_text"].strip())

        if len(chunk_summaries) == 1:
            return chunk_summaries[0]

        merged = "\n".join(chunk_summaries)
        final_result = summarizer(
            merged,
            max_length=260,
            min_length=80,
            do_sample=False,
            truncation=True,
        )
        return final_result[0]["summary_text"].strip()

    def _chunk_text(self, text: str, max_chars: int) -> List[str]:
        """Split long transcript into character-bounded chunks for HF models."""
        cleaned = (text or "").strip()
        if not cleaned:
            return []

        if len(cleaned) <= max_chars:
            return [cleaned]

        paragraphs = [p.strip() for p in cleaned.split("\n") if p.strip()]
        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)

            if para_len > max_chars:
                if current:
                    chunks.append("\n".join(current))
                    current = []
                    current_len = 0

                for i in range(0, para_len, max_chars):
                    chunks.append(para[i:i + max_chars])
                continue

            projected = current_len + para_len + (1 if current else 0)
            if projected > max_chars and current:
                chunks.append("\n".join(current))
                current = [para]
                current_len = para_len
            else:
                current.append(para)
                current_len = projected

        if current:
            chunks.append("\n".join(current))

        return chunks
    
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
Aşağıdaki toplantı transkriptini ayrıntılı biçimde analiz edin ve kapsamlı, uzun bir özet oluşturun.
Her bölümü mümkün olduğunca ayrıntılı doldurun; kısa tutmaya çalışmayın.

Özet aşağıdaki bölümleri içermelidir:

1. **GENEL ÖZET**
   - Toplantının ana konusu, amacı ve bağlamı
   - Katılımcı sayısı ve genel atmosfer
   - Toplantının süresi ve kapsamı hakkında genel izlenim

2. **KATILIMCILAR VE ROLLER**
   - Transkriptten tespit edilen konuşmacılar ve varsa unvanları/rolleri
   - Her konuşmacının toplantıdaki katkı odağı

3. **DETAYLI KONU BAŞLIKLARI**
   - Tartışılan her konuyu ayrı başlık altında ele alın
   - Her konu için: ne tartışıldı, hangi görüşler dile getirildi, hangi sorunlar öne çıktı
   - Konuların birbirleriyle ilişkisi

4. **ÖNEMLİ KARARLAR**
   - Alınan tüm kararları madde madde listeleyin
   - Kararın kim tarafından önerildiği / kimin onayladığı (biliniyorsa)
   - Karara zemin hazırlayan tartışma özeti

5. **EYLEM MADDELERİ**
   - Yapılması gereken her görevi listeleyin
   - Sorumlu kişi / ekip (bahsedildiyse)
   - Teslim tarihi veya süre (bahsedildiyse)
   - Öncelik seviyesi (tartışmadan çıkarılabiliyorsa)

6. **ÖNEMLİ RAKAMLAR, TARİHLER VE VERİLER**
   - Toplantıda geçen bütçe, fiyat, yüzde, adet gibi sayısal bilgiler
   - Bahsedilen tarihler, son teslim tarihleri, kilometre taşları
   - Referans verilen belgeler, sistemler veya araçlar

7. **ÖNEMLI ALINTI VE VURGULAR**
   - Bir konuşmacının özellikle vurguladığı kritik ifadeler (kısa alıntı şeklinde)
   - Anlaşmazlık veya uzlaşma noktaları

8. **SONUÇLAR VE SONRAKİ ADIMLAR**
   - Toplantının genel sonuçları ve başarılan hedefler
   - Çözüme kavuşturulamayan açık konular
   - Planlanan takip toplantıları veya iletişimler
   - Kısa vadeli ve uzun vadeli beklentiler

TRANSKRIPT:
{transcript}
"""
        else:
            prompt = f"""
Analyze the following meeting transcript thoroughly and produce a detailed, long-form summary.
Do not truncate or abbreviate — populate every section as fully as the transcript allows.

The summary must include the following sections:

1. **EXECUTIVE SUMMARY**
   - Main topic, purpose, and context of the meeting
   - Overall tone and outcome in 3–5 sentences
   - High-level takeaway for someone who was not present

2. **PARTICIPANTS AND ROLES**
   - Speakers identified in the transcript and their apparent roles/titles
   - Each participant's primary area of contribution during the meeting

3. **DETAILED DISCUSSION POINTS**
   - Cover every significant topic discussed, each under its own sub-heading
   - For each topic: what was discussed, which viewpoints were raised, what problems or concerns emerged
   - Note any disagreements or differing perspectives between participants
   - Describe how topics related to or built upon each other

4. **DECISIONS MADE**
   - List every decision reached, with full context
   - Who proposed / endorsed each decision (if identifiable)
   - Brief rationale or discussion that led to the decision

5. **ACTION ITEMS**
   - Every task or follow-up commitment mentioned
   - Responsible person or team (if stated)
   - Deadline or timeframe (if stated)
   - Implied priority based on the discussion tone

6. **KEY FIGURES, DATES, AND DATA**
   - All numerical data: budgets, prices, percentages, quantities, metrics
   - Specific dates, deadlines, and milestones mentioned
   - Referenced documents, systems, tools, or external resources

7. **NOTABLE QUOTES AND HIGHLIGHTS**
   - Critical statements made by participants (brief verbatim or near-verbatim)
   - Points of strong agreement or contention
   - Any risks, blockers, or concerns explicitly raised

8. **CONCLUSIONS AND NEXT STEPS**
   - Overall outcomes and goals achieved
   - Open issues that were not resolved
   - Planned follow-up meetings or communications
   - Short-term and long-term expectations going forward

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
