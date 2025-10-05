# services/mcp_service.py - MCP Server Service
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
from services.financial_service import FinancialService
from pydantic import BaseModel
import httpx
import json


OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"
OLLAMA_TIMEOUT = 30
ENABLE_OLLAMA = True

class ChatResponse(BaseModel):


    
    response: str
    type: str = "text"
    data: Optional[Dict] = None
    timestamp: datetime
    suggestions: Optional[List[str]] = None

class MCPService:
    """Model Context Protocol Service for intelligent query routing"""
    
    def __init__(self):
        self.financial_service = FinancialService()
        self.intent_patterns = self._initialize_intent_patterns()
    
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
    
    def detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return intent
        
        return "general"
    
    def extract_numbers(self, text: str) -> List[float]:
        """Extract numbers from text"""
        # Remove commas and extract numbers
        numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', text.replace(',', ''))
        return [float(n) for n in numbers]
    
    def process_query(
        self,
        message: str,
        session_id: str,
        context: Optional[Dict] = None
    ) -> ChatResponse:
        """Process user query through MCP server"""
        
        intent = self.detect_intent(message)
        
        # Route to appropriate handler
        if intent == "calculation":
            return self._handle_calculation(message, context)
        elif intent == "eligibility":
            return self._handle_eligibility(message, context)
        elif intent == "comparison":
            return self._handle_comparison(message, context)
        elif intent == "product_info":
            return self._handle_product_info(message, context)
        elif intent == "application":
            return self._handle_application(message, context)
        elif intent == "affordability":
            return self._handle_affordability(message, context)
        elif intent == "early_payoff":
            return self._handle_early_payoff(message, context)
        elif intent == "greeting":
            return self._handle_greeting(message, context)
        elif intent == "help":
            return self._handle_help(message, context)
        elif intent == "thanks":
            return self._handle_thanks(message, context)
        else:
            return self._handle_general(message, context)
    
    def _handle_calculation(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle loan calculation requests"""
        numbers = self.extract_numbers(message)
        
        if len(numbers) >= 3:
            principal, rate, years = numbers[0], numbers[1], int(numbers[2])
            result = self.financial_service.calculate_loan_payment(principal, rate, years)
            
            response_text = f"""**💰 Loan Payment Calculator**

**Loan Details:**
• Principal Amount: ${result['principal']:,.2f}
• Interest Rate: {result['rate']}% per annum
• Loan Term: {result['term_years']} years

**Payment Breakdown:**
• Monthly Payment: **${result['monthly_payment']:,.2f}**
• Total Payment: ${result['total_payment']:,.2f}
• Total Interest: ${result['total_interest']:,.2f}

Your monthly EMI would be **${result['monthly_payment']:,.2f}**."""
            
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
        else:
            response_text = """To calculate your loan payment, I need:

1. **Loan amount** (e.g., $50,000)
2. **Annual interest rate** (e.g., 8.5%)
3. **Loan term in years** (e.g., 5 years)

**Example:** "Calculate payment for $50,000 at 8.5% for 5 years"

What loan amount are you considering?"""
            
            return ChatResponse(
                response=response_text,
                type="text",
                timestamp=datetime.now()
            )
    
    def _handle_eligibility(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle eligibility check requests"""
        numbers = self.extract_numbers(message)
        
        if len(numbers) >= 3:
            income, credit_score, debt = numbers[0], int(numbers[1]), numbers[2]
            result = self.financial_service.check_eligibility(income, credit_score, debt)
            
            status_emoji = "✅" if result['approved'] else "⚠️"
            
            response_text = f"""**{status_emoji} Loan Eligibility Assessment**

**Your Profile:**
• Annual Income: ${income:,.2f}
• Credit Score: {credit_score}
• Existing Debt: ${debt:,.2f}

**Assessment Result:** **{result['eligibility']}**
**Status:** {"✓ Pre-Qualified" if result['approved'] else "✗ Not Qualified"}

• Maximum Loan Amount: **${result['max_loan_amount']:,.2f}**
• Rate Adjustment: {result['rate_adjustment']:+.1f}%

**Recommendation:** {result['recommendation']}"""
            
            suggestions = [
                "Calculate monthly payment",
                "Compare loan products",
                "Start application"
            ] if result['approved'] else [
                "How to improve credit score",
                "Debt reduction tips",
                "View loan requirements"
            ]
            
            return ChatResponse(
                response=response_text,
                type="eligibility",
                data=result,
                timestamp=datetime.now(),
                suggestions=suggestions
            )
        else:
            response_text = """To check your eligibility, please provide:

1. **Annual income** (e.g., $60,000)
2. **Credit score** (e.g., 720)
3. **Existing debt** (e.g., $15,000)

**Example:** "Check eligibility: income $60,000, credit score 720, debt $15,000"

What's your annual income?"""
            
            return ChatResponse(
                response=response_text,
                type="text",
                timestamp=datetime.now()
            )
    
    def _handle_comparison(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle loan comparison requests"""
        numbers = self.extract_numbers(message)
        
        if len(numbers) >= 2:
            amount, years = numbers[0], int(numbers[1])
            result = self.financial_service.compare_loans(amount, years)
            
            if result['comparisons']:
                response_text = f"**🔍 Loan Comparison for ${amount:,.0f} over {years} years**\n\n"
                
                for comp in result['comparisons']:
                    response_text += f"**{comp['product_name']}**\n"
                    response_text += f"• Interest Rate: {comp['interest_rate']}\n"
                    response_text += f"• Monthly Payment: ${comp['monthly_payment']:,.2f}\n"
                    response_text += f"• Total Interest: ${comp['total_interest']:,.2f}\n\n"
                
                if result.get('best_option'):
                    response_text += f"**💡 Best Option:** {result['best_option']}"
                
                suggestions = [
                    "Check my eligibility",
                    "Calculate exact payment",
                    "Apply for loan"
                ]
            else:
                response_text = f"No loan products available for ${amount:,.0f}. Please try a different amount."
                suggestions = ["View all products", "Check eligibility"]
            
            return ChatResponse(
                response=response_text,
                type="comparison",
                data=result,
                timestamp=datetime.now(),
                suggestions=suggestions
            )
        else:
            response_text = """To compare loans, I need:

1. **Loan amount** (e.g., $50,000)
2. **Term in years** (e.g., 5)

**Example:** "Compare loans for $50,000 over 5 years"

What amount are you looking to borrow?"""
            
            return ChatResponse(
                response=response_text,
                type="text",
                timestamp=datetime.now()
            )
    
    def _handle_product_info(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle product information requests"""
        loan_type = None
        for lt in ["personal", "home", "auto", "business"]:
            if lt in message.lower():
                loan_type = lt
                break
        
        products = self.financial_service.get_loan_products(loan_type)
        
        if loan_type and loan_type in products:
            product = products[loan_type]
            response_text = f"""**{product['name']} Details**

• **Interest Rate Range:** {product['rate_range']}
• **Loan Amount:** ${product['min_amount']:,} - ${product['max_amount']:,}
• **Loan Term:** {product['term_range']}
• **Features:** {product.get('features', 'Flexible repayment options')}

This loan is ideal for {loan_type} financial needs."""
            
            suggestions = [
                f"Calculate {loan_type} loan payment",
                "Check eligibility",
                f"Compare {loan_type} loans"
            ]
        else:
            response_text = "**🏦 Available Loan Products**\n\n"
            for key, product in products.items():
                response_text += f"**{product['name']}**\n"
                response_text += f"• Rates: {product['rate_range']}\n"
                response_text += f"• Amount: ${product['min_amount']:,} - ${product['max_amount']:,}\n"
                response_text += f"• Term: {product['term_range']}\n\n"
            
            suggestions = [
                "Personal loan details",
                "Home loan details",
                "Compare all loans"
            ]
        
        return ChatResponse(
            response=response_text,
            type="product_info",
            data={"products": products},
            timestamp=datetime.now(),
            suggestions=suggestions
        )
    
    def _handle_application(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle loan application requests"""
        response_text = """**📋 Start Your Loan Application**

To begin, I'll guide you through the process:

**Step 1: Choose Loan Type**
• Personal Loan
• Home Loan
• Auto Loan
• Business Loan

**Step 2: Check Eligibility**
We'll verify your:
• Income and employment
• Credit score
• Existing debts

**Step 3: Submit Documents**
• ID proof
• Income proof
• Address proof

**Step 4: Review & Submit**

Which loan type are you interested in?"""
        
        suggestions = [
            "Personal loan application",
            "Check my eligibility first",
            "What documents needed?"
        ]
        
        return ChatResponse(
            response=response_text,
            type="application",
            timestamp=datetime.now(),
            suggestions=suggestions
        )
    
    def _handle_affordability(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle affordability calculation requests"""
        numbers = self.extract_numbers(message)
        
        if len(numbers) >= 2:
            income, expenses = numbers[0], numbers[1]
            term = int(numbers[2]) if len(numbers) >= 3 else 5
            
            result = self.financial_service.calculate_affordability(income, expenses, term)
            
            response_text = f"""**💵 Affordability Analysis**

**Your Financial Profile:**
• Monthly Income: ${income:,.2f}
• Monthly Expenses: ${expenses:,.2f}
• Available for EMI: ${result['available_for_emi']:,.2f}

**Maximum Affordable Loan:**
• Loan Amount: **${result['max_loan_amount']:,.2f}**
• Term: {term} years
• Estimated Monthly EMI: ${result['estimated_emi']:,.2f}

**Debt-to-Income Ratio:** {result['dti_ratio']}%
**Status:** {result['affordability_status']}"""
            
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
        else:
            response_text = """To calculate affordability, I need:

1. **Monthly income** (e.g., $5,000)
2. **Monthly expenses** (e.g., $2,500)
3. **Desired term** (e.g., 5 years) - optional

**Example:** "Can I afford a loan with income $5,000 and expenses $2,500?"

What's your monthly income?"""
            
            return ChatResponse(
                response=response_text,
                type="text",
                timestamp=datetime.now()
            )
    
    def _handle_early_payoff(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle early payoff calculation requests"""
        numbers = self.extract_numbers(message)
        
        if len(numbers) >= 4:
            principal, rate, years, extra = numbers[0], numbers[1], int(numbers[2]), numbers[3]
            result = self.financial_service.calculate_early_payoff(principal, rate, years, extra)
            
            response_text = f"""**⚡ Early Payoff Calculator**

**Original Loan:**
• Monthly Payment: ${result['original_monthly']:,.2f}
• Total Interest: ${result['original_interest']:,.2f}
• Payoff Time: {result['original_months']} months

**With Extra ${extra:,.2f}/month:**
• New Monthly Payment: ${result['new_monthly']:,.2f}
• New Total Interest: ${result['new_interest']:,.2f}
• New Payoff Time: {result['new_months']} months

**💰 Savings:**
• Interest Saved: **${result['interest_saved']:,.2f}**
• Time Saved: **{result['months_saved']} months**

You'll pay off your loan {result['months_saved']} months earlier and save ${result['interest_saved']:,.2f}!"""
            
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
            response_text = """To calculate early payoff savings, I need:

1. **Loan amount** (e.g., $50,000)
2. **Interest rate** (e.g., 8.5%)
3. **Loan term** (e.g., 5 years)
4. **Extra monthly payment** (e.g., $200)

**Example:** "Calculate early payoff for $50,000 at 8.5% for 5 years with $200 extra"

What's your current loan amount?"""
            
            return ChatResponse(
                response=response_text,
                type="text",
                timestamp=datetime.now()
            )
    
    def _handle_greeting(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle greeting messages"""
        response_text = """Hello! 👋 Welcome to our Financial Services.

I'm your AI financial assistant. I can help you with:

• **Calculate** loan payments and EMI
• **Check** your loan eligibility
• **Compare** different loan products
• **Find** the best rates
• **Start** your loan application
• **Calculate** affordability and early payoff

What would you like to explore today?"""
        
        suggestions = [
            "Calculate loan payment",
            "Check eligibility",
            "View loan products"
        ]
        
        return ChatResponse(
            response=response_text,
            type="greeting",
            timestamp=datetime.now(),
            suggestions=suggestions
        )
    
    def _handle_help(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle help requests"""
        response_text = """**🤖 How I Can Help You**

**Loan Calculations:**
"Calculate payment for $50,000 at 8.5% for 5 years"

**Eligibility Checks:**
"Check eligibility: income $60,000, credit score 720, debt $15,000"

**Loan Comparisons:**
"Compare loans for $50,000 over 5 years"

**Product Information:**
"What are personal loan rates?" or "Show me all loan products"

**Affordability:**
"Can I afford a loan with income $5,000 and expenses $2,500?"

**Applications:**
"I want to apply for a home loan"

Just ask naturally, and I'll guide you!"""
        
        suggestions = [
            "Calculate a loan",
            "Check eligibility",
            "Compare products"
        ]
        
        return ChatResponse(
            response=response_text,
            type="help",
            timestamp=datetime.now(),
            suggestions=suggestions
        )
    
    def _handle_thanks(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle thank you messages"""
        response_text = """You're welcome! 😊

Is there anything else I can help you with?

• Calculate another loan
• Check different scenarios
• Compare more products
• Start an application"""
        
        suggestions = [
            "Calculate loan payment",
            "Check eligibility",
            "View all products"
        ]
        
        return ChatResponse(
            response=response_text,
            type="thanks",
            timestamp=datetime.now(),
            suggestions=suggestions
        )
    
    def _handle_general(self, message: str, context: Optional[Dict]) -> ChatResponse:
        """Handle general queries"""
        response_text = """I'm here to help with your financial needs! I specialize in:

**💰 Loan Services:**
• Personal loans
• Home loans
• Auto loans
• Business loans

**🔢 Calculations:**
• Monthly payment estimates
• Total interest calculations
• Affordability analysis
• Early payoff scenarios

**✅ Eligibility:**
• Quick pre-qualification
• Credit assessment
• Maximum loan amount

**📊 Comparisons:**
• Compare rates and terms
• Find best options
• Side-by-side analysis

What specific information are you looking for?"""
        
        suggestions = [
            "Calculate loan payment",
            "Check my eligibility",
            "Compare loan options",
            "View current rates"
        ]
        
        return ChatResponse(
            response=response_text,
            type="general",
            timestamp=datetime.now(),
            suggestions=suggestions
        )