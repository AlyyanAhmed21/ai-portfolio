import ollama
from fastapi import APIRouter
from app.schemas.chat_schemas import ChatRequest, ChatResponse
from app.services.rag_service import rag_service_instance

router = APIRouter()

# --- NEW, "EXECUTIVE" PROMPT TEMPLATE ---
PROMPT_TEMPLATE = """
### ROLE ###
You are an expert AI assistant for Alyyan Ahmed's professional portfolio, named "PortfolioAI".
You must be professional, articulate, and provide well-structured, readable answers.

### TASK ###
Your task is to answer questions about Alyyan Ahmed based *exclusively* on the provided context information.
Do not use any external knowledge.

### FORMATTING RULES ###
- **Use Markdown for all formatting.**
- Use **bolding** for emphasis on key terms, technologies, or titles.
- Use bullet points (using `-`) for lists of skills, projects, or responsibilities.
- Keep answers concise and to the point.

### BEHAVIORAL RULES ###
1.  **Analyze the User's Question:** Understand the user's intent.
2.  **Scan the Context:** Find the answer only within the provided context.
3.  **Synthesize a Professional Answer:** Formulate a direct answer using the specified Markdown formatting.
4.  **Handle Missing Information:** If the answer is not in the context, you MUST state: "Based on the provided information, I cannot answer that question." Do not apologize or guess.
5.  **Self-Awareness:** If the user asks about "you" (the AI), your purpose, or your architecture, you MUST prioritize information from context that has the source 'self'.

### CONTEXT ###
{context}

### USER QUESTION ###
{question}

### YOUR ANSWER (in Markdown) ###
"""

@router.post("/chat", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """
    Receives a message, routes it to the correct knowledge base,
    retrieves context, and generates a context-aware answer.
    """
    try:
        question = request.message
        print(f"Received question: {question}")

        # 1. Route the query to determine the correct knowledge base
        category = rag_service_instance.route_query(question)
        
        # 2. Get the appropriate retriever
        retriever = rag_service_instance.get_retriever(category)
        
        if retriever is None:
             return ChatResponse(answer="Knowledge base is not available.")
        
        # 3. Retrieve relevant context from the chosen knowledge base
        relevant_docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        print(f"--- Retrieved Context from '{category}' ---\n{context}\n-------------------------")

        # 4. Generate the final answer
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)
        response = ollama.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        answer = response['message']['content']
        return ChatResponse(answer=answer)

    except Exception as e:
        print(f"An error occurred in the chat endpoint: {e}")
        return ChatResponse(answer="Sorry, I encountered an error. Please try again.")