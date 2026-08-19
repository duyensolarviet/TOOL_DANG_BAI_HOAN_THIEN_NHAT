import google.generativeai as genai

class GeminiHelper:
    def __init__(self, api_key=None, model_name='gemini-flash-lite-latest'):
        self.api_key = api_key
        self.model_name = model_name
        self.fallback_models = [
            'gemini-flash-lite-latest',
            'gemini-flash-latest',
            'gemini-3.5-flash-lite',
            'gemini-3.5-flash'
        ]
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)

    def set_api_key(self, api_key):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def rewrite_content(self, original_text, prompt):
        """
        Viết lại nội dung bằng Gemini AI (Hạn mức 1.500 bài/ngày với model 2.0 Flash)
        """
        if not self.api_key:
            raise ValueError("Chưa cấu hình API Key của Gemini!")
            
        full_prompt = f"{prompt}\n\nNội dung gốc:\n{original_text}\n\nNội dung mới (chỉ trả về nội dung, không giải thích):"
        
        last_exception = None
        # Thử các model 1.500 lượt/ngày: gemini-2.0-flash -> gemini-2.0-flash-lite -> gemini-1.5-flash
        for m_name in self.fallback_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(full_prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                last_exception = e
                print(f"Lỗi khi gọi Gemini API ({m_name}): {e}")
                continue
                
        if last_exception:
            raise last_exception
        return original_text

try:
    from groq import Groq
except ImportError:
    Groq = None

class GroqHelper:
    def __init__(self, api_key=None, model="llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model
        if self.api_key and Groq:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None

    def rewrite_content(self, original_text, prompt):
        """
        Viết lại nội dung bằng Groq AI
        """
        if not self.api_key or not self.client:
            raise ValueError("Chưa cấu hình API Key của Groq hoặc chưa cài thư viện groq!")
            
        full_prompt = f"{prompt}\n\nNội dung gốc:\n{original_text}\n\nNội dung mới (chỉ trả về nội dung, không giải thích):"
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt,
                    }
                ],
                model=self.model,
            )
            if chat_completion.choices and chat_completion.choices[0].message.content:
                return chat_completion.choices[0].message.content.strip()
            return original_text
        except Exception as e:
            print(f"Lỗi khi gọi Groq API: {e}")
            raise e
