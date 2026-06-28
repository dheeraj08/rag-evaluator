from langchain_ollama import OllamaLLM
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re
import os

def get_llm():
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        return ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key)
    return OllamaLLM(model="llama3.2")

def extract_score(text: str) -> float:
    match = re.search(r'SCORE:\s*([0-9.]+)', text)
    if match:
        return round(min(max(float(match.group(1)), 0.0), 1.0), 2)
    numbers = re.findall(r'([0-9.]+)', text)
    for n in numbers:
        try:
            val = float(n)
            if 0.0 <= val <= 1.0:
                return round(val, 2)
        except:
            pass
    return 0.5

def extract_reasoning(text: str) -> str:
    match = re.search(r'REASONING:\s*(.+?)(?=SCORE:|$)', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text[:200].strip()

def score_context_precision(question: str, context: str) -> dict:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""Rate how useful this retrieved context is for answering the question. High precision means the context contains exactly what is needed.

Question: {question}

Context: {context}

You MUST respond in exactly this format and nothing else:
REASONING: <one sentence explanation>
SCORE: <number between 0.0 and 1.0>""")

    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"question": question, "context": context})
    return {
        "score": extract_score(result),
        "reasoning": extract_reasoning(result),
        "raw": result
    }
