# services/mcp_service.py - Enhanced MCP Server Service with Ollama Integration
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
from services.financial_service import FinancialService
from pydantic import BaseModel
import httpx
import json
from logging import Logger
import asyncio

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "deepseek-r1:7b"
OLLAMA_TIMEOUT = 60
ENABLE_OLLAMA = True

class ChatResponse(BaseModel):
    response: str
    type: str = "text"
    data: Optional[Dict] = None
    timestamp: datetime
    suggestions: Optional[List[str]] = None

class MCPService:
    """Model Context Protocol Service with Ollama integration for intelligent query routing"""
    
    def __init__(self):
        self.financial_service = FinancialService()
        self.intent_patterns = self._initialize_intent_patterns()
        self.system_prompt = self._initialize_system_prompt()
    
    def _initialize_system_prompt(self) -> str:
        """Initialize system prompt for Ollama"""
        return """You are a financial assistant AI for a loan servicing platform. Your role is to:

1. Understand user queries about loans, financial calculations, and eligibility
2. Extract relevant financial information (amounts, rates, terms, income, etc.)
3. Determine what financial function should be called
4. Provide natural, helpful responses

Available Functions:
- calculate_loan_payment: Calculate EMI and loan details (needs: principal, rate, years)
- check_eligibility: Check loan eligibility (needs: income, credit_score, existing_debt)
- compare_loans: Compare loan products (needs: amount, term, optional credit_score)
- get_loan_products: Get information about loan types
- calculate_affordability: Calculate max affordable loan (needs: income, expenses, term)
- calculate_early_payoff: Calculate early payoff savings (needs: principal, rate, years, extra_payment)

When responding:
- Be conversational and helpful
- Extract numbers accurately from user queries
- If information is missing, ask for it naturally
- Format responses in a clear, easy-to-read way
- Provide actionable suggestions

Response Format:
{
    "intent": "calculation|eligibility|comparison|product_info|affordability|early_payoff|greeting|help|general",
    "extracted_data": {
        "principal": number,
        "rate": number,
        "years": number,
        "income": number,
        "credit_score": number,
        "existing_debt": number,
        "extra_payment": number,
        "monthly_expenses": number
    },
    "missing_fields": ["field1", "field2"],
    "response_text": "Natural language response to user",
    "should_call_function": true/false
}

Always respond in valid JSON format."""
    
    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Initialize intent detection patterns"""
        return {
            "calculation": ["calculate", "payment", "monthly", "emi", "how much", "compute"],
            "eligibility": ["eligibility", "eligible", "qualify", "can i get", "approved", "qualify for"],
            "comparison": ["compare", "comparison", "which loan", "best loan", "vs", "versus"],
            "product_info": ["rates", "interest", "loan types", "products", "options", "what loans"],
            "application": ["apply", "application", "start", "begin process", "want to apply"],
            "affordability": ["afford", "can i afford", "maximum", "max loan", "how much can i"],
            "early_payoff": ["early payoff", "pay off early", "extra payment", "prepayment"],
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "help": ["help", "assist", "support", "what can you do", "how can you help"],
            "thanks": ["thank", "thanks", "appreciate", "grateful"]
        }
    
    async def query_ollama(self, user_message: str, context: Optional[Dict] = None) -> Dict:
        """Query Ollama for intelligent response processing"""
        if not ENABLE_OLLAMA:
            return None
        
        try:
            # Build conversation context
            conversation_history = ""
            if context and "history" in context:
                for msg in context["history"][-3:]:  # Last 3 messages for context
                    conversation_history += f"\nUser: {msg.get('user', '')}\nAssistant: {msg.get('assistant', '')}"
            
            prompt = f"""{self.system_prompt}

{conversation_history}

User Query: {user_message}

Analyze this query and respond in JSON format with intent, extracted data, missing fields, and a natural response."""
            
            async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ollama_response = result.get("response", "{}")
                    
                    # Parse JSON response
                    try:
                        parsed_response = json.loads(ollama_response)
                        return parsed_response
                    except json.JSONDecodeError:
                        # Fallback: extract JSON from response
                        json_match = re.search(r'\{.*\}', ollama_response, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                        return None
                else:
                    print(f"Ollama error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error querying Ollama: {str(e)}")
            return None
    
    def detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return intent
        
        return "general"
    
    def extract_numbers(self, text: str) -> List[float]:
        """Extract numbers from text"""
        numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', text.replace(',', ''))
        return [float(n) for n in numbers]
    
    async def process_query(
        self,
        message: str,
        session_id: str,
        context: Optional[Dict] = None
    ) -> ChatResponse:
        
        ollama_result = await self.query_ollama(message, context)
        print("getme response", ollama_result)
        if ollama_result and ENABLE_OLLAMA:
            intent = ollama_result.get("intent", "general")
            extracted_data = ollama_result.get("extracted_data", {"this is not a relevant question  "})
            missing_fields = ollama_result.get("missing_fields", [])
            should_call_function = ollama_result.get("should_call_function", False)
            ollama_response_text = ollama_result.get("response_text", "")


            
            # If we have all data and should call function, execute it
            if should_call_function and not missing_fields:
                return await self._execute_financial_function(
                    intent, 
                    extracted_data, 
                    ollama_response_text,
                    context
                )
            else:
                # Return Ollama's response with suggestions
                suggestions = self._get_suggestions_for_intent(intent)
                return ChatResponse(
                    response=ollama_response_text,
                    type=intent,
                    timestamp=datetime.now(),
                    suggestions=suggestions
                )
        else:
            # Fallback to rule-based processing
            intent = self.detect_intent(message)
            return await self._fallback_processing(message, intent, context)
    
    async def _execute_financial_function(
        self,
        intent: str,
        data: Dict,
        ollama_text: str,
        context: Optional[Dict]
    ) -> ChatResponse:
        """Execute financial service functions based on intent and data"""
        
        try:
            if intent == "calculation":
                result = self.financial_service.calculate_loan_payment(
                    principal=data.get("principal"),
                    annual_rate=data.get("rate"),
                    years=int(data.get("years"))
                )
                
                response_text = self._format_calculation_response(result, ollama_text)
                suggestions = [
                    "Check my eligibility",
                    "Compare different loans",
                    "Calculate with extra payments"
                ]
                
                return ChatResponse(
                    response=response_text,
                    type="calculator",
                    data=result,
                    timestamp=datetime.now(),
                    suggestions=suggestions
                )
            
            elif intent == "eligibility":
                result = self.financial_service.check_eligibility(
                    income=data.get("income"),
                    credit_score=int(data.get("credit_score")),
                    existing_debt=data.get("existing_debt")
                )
                
                response_text = self._format_eligibility_response(result, ollama_text)
                suggestions = self._get_eligibility_suggestions(result)
                
                return ChatResponse(
                    response=response_text,
                    type="eligibility",
                    data=result,
                    timestamp=datetime.now(),
                    suggestions=suggestions
                )
            
            elif intent == "comparison":
                result = self.financial_service.compare_loans(
                    amount=data.get("amount"),
                    term=int(data.get("years") or data.get("term", 5)),
                    credit_score=int(data.get("credit_score")) if data.get("credit_score") else None
                )
                
                response_text = self._format_comparison_response(result, data, ollama_text)
                suggestions = [
                    "Check my eligibility",
                    "Calculate exact payment",
                    "Apply for loan"
                ]
                
                return ChatResponse(
                    response=response_text,
                    type="comparison",
                    data=result,
                    timestamp=datetime.now(),
                    suggestions=suggestions
                )
            
            elif intent == "affordability":
                result = self.financial_service.calculate_affordability(
                    income=data.get("income"),
                    monthly_expenses=data.get("monthly_expenses"),
                    desired_term=int(data.get("years") or data.get("term", 5))
                )
                
                response_text = self._format_affordability_response(result, ollama_text)
                suggestions = [
                    "Calculate exact payment",
                    "Check eligibility",
                    "View loan products"
                ]
                
                return ChatResponse(
                    response=response_text,
                    type="affordability",
                    data=result,
                    timestamp=datetime.now(),
                    suggestions=suggestions
                )
            
            elif intent == "early_payoff":
                result = self.financial_service.calculate_early_payoff(
                    principal=data.get("principal"),
                    annual_rate=data.get("rate"),
                    years=int(data.get("years")),
                    extra_payment=data.get("extra_payment")
                )
                
                response_text = self._format_early_payoff_response(result, ollama_text)
                suggestions = [
                    "Try different extra payment",
                    "Calculate regular payment",
                    "View loan products"
                ]
                
                return ChatResponse(
                    response=response_text,
                    type="early_payoff",
                    data=result,
                    timestamp=datetime.now(),
                    suggestions=suggestions
                )
            
            else:
                # Fallback for other intents
                return await self._fallback_processing("", intent, context)
                
        except Exception as e:
            print(f"Error executing financial function: {str(e)}")
            return ChatResponse(
                response=f"{ollama_text}\n\nI encountered an error processing your request. Please verify your information and try again.",
                type="error",
                timestamp=datetime.now()
            )
    
    def _format_calculation_response(self, result: Dict, ollama_text: str) -> str:
        """Format calculation response with Ollama context"""
        return f"""{ollama_text}

**💰 Loan Payment Details**

**Loan Amount:** ${result['principal']:,.2f}
**Interest Rate:** {result['rate']}% per annum
**Loan Term:** {result['term_years']} years

**Monthly Payment:** **${result['monthly_payment']:,.2f}**
**Total Payment:** ${result['total_payment']:,.2f}
**Total Interest:** ${result['total_interest']:,.2f}"""
    
    def _format_eligibility_response(self, result: Dict, ollama_text: str) -> str:
        """Format eligibility response with Ollama context"""
        status_emoji = "✅" if result['approved'] else "⚠️"
        
        return f"""{ollama_text}

**{status_emoji} Eligibility Assessment**

**Credit Score:** {result['credit_score']}
**Eligibility Level:** {result['eligibility']}
**Status:** {"✓ Pre-Qualified" if result['approved'] else "✗ Not Qualified"}

**Maximum Loan:** ${result['max_loan_amount']:,.2f}
**Rate Adjustment:** {result['rate_adjustment']:+.1f}%

**Recommendation:** {result['recommendation']}"""
    
    def _format_comparison_response(self, result: Dict, data: Dict, ollama_text: str) -> str:
        """Format comparison response with Ollama context"""
        amount = data.get("amount", 0)
        years = data.get("years") or data.get("term", 5)
        
        response = f"""{ollama_text}

**🔍 Loan Comparison for ${amount:,.0f} over {years} years**

"""
        
        for comp in result['comparisons']:
            response += f"""**{comp['product_name']}**
• Interest Rate: {comp['interest_rate']}
• Monthly Payment: ${comp['monthly_payment']:,.2f}
• Total Interest: ${comp['total_interest']:,.2f}

"""
        
        if result.get('best_option'):
            response += f"**💡 Best Option:** {result['best_option']}"
        
        return response
    
    def _format_affordability_response(self, result: Dict, ollama_text: str) -> str:
        """Format affordability response with Ollama context"""
        return f"""{ollama_text}

**💵 Affordability Analysis**

**Available for EMI:** ${result['available_for_emi']:,.2f}
**Maximum Affordable Loan:** **${result['max_loan_amount']:,.2f}**
**Estimated Monthly EMI:** ${result['estimated_emi']:,.2f}

**Debt-to-Income Ratio:** {result['dti_ratio']}%
**Status:** {result['affordability_status']}"""
    
    def _format_early_payoff_response(self, result: Dict, ollama_text: str) -> str:
        """Format early payoff response with Ollama context"""
        return f"""{ollama_text}

**⚡ Early Payoff Analysis**

**Original Loan:**
• Monthly Payment: ${result['original_monthly']:,.2f}
• Total Interest: ${result['original_interest']:,.2f}
• Payoff Time: {result['original_months']} months

**With Extra Payment:**
• New Monthly: ${result['new_monthly']:,.2f}
• New Interest: ${result['new_interest']:,.2f}
• New Payoff: {result['new_months']} months

**💰 Savings:**
• Interest Saved: **${result['interest_saved']:,.2f}**
• Time Saved: **{result['months_saved']} months**"""
    
    def _get_eligibility_suggestions(self, result: Dict) -> List[str]:
        """Get suggestions based on eligibility result"""
        if result['approved']:
            return [
                "Calculate monthly payment",
                "Compare loan products",
                "Start application"
            ]
        else:
            return [
                "How to improve credit score",
                "Debt reduction tips",
                "View loan requirements"
            ]
    
    def _get_suggestions_for_intent(self, intent: str) -> List[str]:
        """Get suggestions based on intent"""
        suggestions_map = {
            "calculation": ["Check eligibility", "Compare loans", "View products"],
            "eligibility": ["Calculate payment", "Compare products", "Apply now"],
            "comparison": ["Check eligibility", "Calculate payment", "Apply now"],
            "product_info": ["Calculate payment", "Check eligibility", "Compare loans"],
            "affordability": ["Calculate payment", "Check eligibility", "View products"],
            "early_payoff": ["Try different amount", "View products", "Calculate payment"],
            "greeting": ["Calculate loan", "Check eligibility", "View products"],
            "help": ["Calculate loan", "Check eligibility", "Compare products"],
            "general": ["Calculate loan", "Check eligibility", "View products"]
        }
        return suggestions_map.get(intent, ["Calculate loan", "Check eligibility", "View products"])
    
    async def _fallback_processing(
        self,
        message: str,
        intent: str,
        context: Optional[Dict]
    ) -> ChatResponse:
        """Fallback to rule-based processing when Ollama is unavailable"""
        
        fallback_responses = {
            "greeting": "Hello! 👋 I'm your financial assistant. I can help with loan calculations, eligibility checks, and more. What would you like to know?",
            "help": "I can help you with:\n• Loan calculations\n• Eligibility checks\n• Loan comparisons\n• Product information\n• Affordability analysis\n\nWhat would you like to explore?",
            "thanks": "You're welcome! 😊 Is there anything else I can help you with?",
            "general": "I'm here to help with your financial needs. I can calculate loan payments, check eligibility, compare products, and more. What would you like to know?"
        }
        
        response_text = fallback_responses.get(intent, fallback_responses["general"])
        suggestions = self._get_suggestions_for_intent(intent)
        
        return ChatResponse(
            response=response_text,
            type=intent,
            timestamp=datetime.now(),
            suggestions=suggestions
        )