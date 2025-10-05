# services/financial_service.py - Financial Calculations Service
from typing import Dict, List, Optional
from datetime import datetime

# Loan product database
LOAN_PRODUCTS = {
    "personal": {
        "name": "Personal Loan",
        "rate_range": "8.5% - 14.5%",
        "min_amount": 5000,
        "max_amount": 50000,
        "term_range": "1-5 years",
        "features": "Quick approval, minimal documentation"
    },
    "home": {
        "name": "Home Loan",
        "rate_range": "6.5% - 9.5%",
        "min_amount": 100000,
        "max_amount": 5000000,
        "term_range": "5-30 years",
        "features": "Low interest rates, tax benefits"
    },
    "auto": {
        "name": "Auto Loan",
        "rate_range": "7.5% - 12.5%",
        "min_amount": 10000,
        "max_amount": 200000,
        "term_range": "1-7 years",
        "features": "New and used car financing"
    },
    "business": {
        "name": "Business Loan",
        "rate_range": "9.5% - 16.5%",
        "min_amount": 25000,
        "max_amount": 1000000,
        "term_range": "1-10 years",
        "features": "Working capital, expansion, equipment"
    }
}

class FinancialService:
    """Service for financial calculations and loan operations"""
    
    def calculate_loan_payment(
        self,
        principal: float,
        annual_rate: float,
        years: int,
        include_schedule: bool = False
    ) -> Dict:
        """
        Calculate monthly loan payment using amortization formula
        
        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (percentage)
            years: Loan term in years
            include_schedule: Whether to include amortization schedule
        
        Returns:
            Dictionary with payment details
        """
        monthly_rate = annual_rate / 100 / 12
        num_payments = years * 12
        
        if monthly_rate == 0:
            monthly_payment = principal / num_payments
        else:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / \
                            ((1 + monthly_rate)**num_payments - 1)
        
        total_payment = monthly_payment * num_payments
        total_interest = total_payment - principal
        
        result = {
            "monthly_payment": round(monthly_payment, 2),
            "total_payment": round(total_payment, 2),
            "total_interest": round(total_interest, 2),
            "principal": principal,
            "rate": annual_rate,
            "term_years": years
        }
        
        if include_schedule:
            result["amortization_schedule"] = self._generate_amortization_schedule(
                principal, monthly_rate, monthly_payment, num_payments
            )
        
        return result
    
    def _generate_amortization_schedule(
        self,
        principal: float,
        monthly_rate: float,
        monthly_payment: float,
        num_payments: int
    ) -> List[Dict]:
        """Generate amortization schedule"""
        schedule = []
        balance = principal
        
        for month in range(1, min(num_payments + 1, 13)):  # First 12 months only
            interest_payment = balance * monthly_rate
            principal_payment = monthly_payment - interest_payment
            balance -= principal_payment
            
            schedule.append({
                "month": month,
                "payment": round(monthly_payment, 2),
                "principal": round(principal_payment, 2),
                "interest": round(interest_payment, 2),
                "balance": round(max(0, balance), 2)
            })
        
        return schedule
    
    def check_eligibility(
        self,
        income: float,
        credit_score: int,
        existing_debt: float,
        employment_years: Optional[int] = None
    ) -> Dict:
        """
        Check loan eligibility based on financial metrics
        
        Args:
            income: Annual income
            credit_score: Credit score (300-850)
            existing_debt: Existing debt amount
            employment_years: Years in current employment
        
        Returns:
            Dictionary with eligibility assessment
        """
        # Calculate debt-to-income ratio
        max_loan = income * 4  # Simple DTI calculation
        available_loan = max(0, max_loan - existing_debt)
        
        # Determine eligibility based on credit score
        if credit_score >= 750:
            eligibility = "Excellent"
            rate_discount = 2.0
            recommendation = "You qualify for the best rates and terms available!"
        elif credit_score >= 700:
            eligibility = "Good"
            rate_discount = 1.0
            recommendation = "You qualify for competitive rates. Consider improving your score for better terms."
        elif credit_score >= 650:
            eligibility = "Fair"
            rate_discount = 0
            recommendation = "You may qualify with standard terms. Improving your credit score could help."
        else:
            eligibility = "Poor"
            rate_discount = -2.0
            recommendation = "Consider improving your credit score and reducing debt before applying."
        
        # Employment stability bonus
        if employment_years and employment_years >= 2:
            rate_discount += 0.5
        
        approved = credit_score >= 650 and available_loan > 0
        
        return {
            "eligibility": eligibility,
            "max_loan_amount": round(available_loan, 2),
            "credit_score": credit_score,
            "rate_adjustment": round(rate_discount, 1),
            "approved": approved,
            "recommendation": recommendation
        }
    
    def compare_loans(
        self,
        amount: float,
        term: int,
        credit_score: Optional[int] = None
    ) -> Dict:
        """
        Compare different loan products
        
        Args:
            amount: Loan amount
            term: Loan term in years
            credit_score: Credit score for personalized rates
        
        Returns:
            Dictionary with loan comparisons
        """
        comparisons = []
        
        for key, product in LOAN_PRODUCTS.items():
            if amount >= product["min_amount"] and amount <= product["max_amount"]:
                # Use middle of rate range
                rate_parts = product["rate_range"].split(" - ")
                min_rate = float(rate_parts[0].strip('%'))
                max_rate = float(rate_parts[1].strip('%'))
                avg_rate = (min_rate + max_rate) / 2
                
                # Adjust rate based on credit score
                if credit_score:
                    if credit_score >= 750:
                        avg_rate = min_rate
                    elif credit_score >= 700:
                        avg_rate = min_rate + (max_rate - min_rate) * 0.3
                    elif credit_score >= 650:
                        avg_rate = min_rate + (max_rate - min_rate) * 0.6
                    else:
                        avg_rate = max_rate
                
                payment_info = self.calculate_loan_payment(amount, avg_rate, term)
                
                comparisons.append({
                    "product_type": key,
                    "product_name": product["name"],
                    "interest_rate": f"{avg_rate:.2f}%",
                    "monthly_payment": payment_info["monthly_payment"],
                    "total_interest": payment_info["total_interest"],
                    "eligibility_score": self._get_eligibility_score(credit_score) if credit_score else None
                })
        
        # Sort by monthly payment
        comparisons.sort(key=lambda x: x["monthly_payment"])
        
        best_option = comparisons[0]["product_name"] if comparisons else None
        
        return {
            "comparisons": comparisons,
            "best_option": best_option,
            "total_products": len(comparisons)
        }
    
    def _get_eligibility_score(self, credit_score: int) -> str:
        """Get eligibility score label"""
        if credit_score >= 750:
            return "Excellent"
        elif credit_score >= 700:
            return "Good"
        elif credit_score >= 650:
            return "Fair"
        else:
            return "Poor"
    
    def get_loan_products(self, loan_type: Optional[str] = None) -> Dict:
        """
        Get loan product information
        
        Args:
            loan_type: Specific loan type to fetch (optional)
        
        Returns:
            Dictionary of loan products
        """
        if loan_type and loan_type.lower() in LOAN_PRODUCTS:
            return {loan_type.lower(): LOAN_PRODUCTS[loan_type.lower()]}
        return LOAN_PRODUCTS
    
    def get_current_rates(self) -> Dict:
        """Get current interest rates for all products"""
        rates = {}
        for key, product in LOAN_PRODUCTS.items():
            rates[key] = {
                "name": product["name"],
                "rate_range": product["rate_range"],
                "updated_at": datetime.now().isoformat()
            }
        
        rates["updated_at"] = datetime.now().isoformat()
        return rates
    
    def calculate_affordability(
        self,
        income: float,
        monthly_expenses: float,
        desired_term: int
    ) -> Dict:
        """
        Calculate maximum affordable loan amount
        
        Args:
            income: Monthly income
            monthly_expenses: Monthly expenses
            desired_term: Desired loan term in years
        
        Returns:
            Dictionary with affordability details
        """
        # Calculate available income for EMI (typically 40-50% of disposable income)
        disposable_income = income - monthly_expenses
        max_emi = disposable_income * 0.45  # 45% of disposable income
        
        # Calculate DTI ratio
        dti_ratio = (monthly_expenses / income) * 100 if income > 0 else 0
        
        # Estimate max loan using average interest rate of 9%
        avg_rate = 9.0
        monthly_rate = avg_rate / 100 / 12
        num_payments = desired_term * 12
        
        if monthly_rate > 0 and max_emi > 0:
            max_loan = max_emi * ((1 + monthly_rate)**num_payments - 1) / \
                      (monthly_rate * (1 + monthly_rate)**num_payments)
        else:
            max_loan = 0
        
        # Determine affordability status
        if dti_ratio < 30:
            status = "Excellent affordability"
        elif dti_ratio < 40:
            status = "Good affordability"
        elif dti_ratio < 50:
            status = "Fair affordability"
        else:
            status = "Limited affordability"
        
        return {
            "max_loan_amount": round(max_loan, 2),
            "available_for_emi": round(max_emi, 2),
            "estimated_emi": round(max_emi, 2),
            "dti_ratio": round(dti_ratio, 1),
            "affordability_status": status,
            "disposable_income": round(disposable_income, 2)
        }
    
    def calculate_early_payoff(
        self,
        principal: float,
        annual_rate: float,
        years: int,
        extra_payment: float
    ) -> Dict:
        """
        Calculate savings from making extra payments
        
        Args:
            principal: Loan amount
            annual_rate: Annual interest rate
            years: Original loan term
            extra_payment: Extra monthly payment amount
        
        Returns:
            Dictionary with early payoff analysis
        """
        # Original loan calculation
        original = self.calculate_loan_payment(principal, annual_rate, years)
        original_monthly = original["monthly_payment"]
        original_interest = original["total_interest"]
        original_months = years * 12
        
        # Calculate new payoff with extra payment
        monthly_rate = annual_rate / 100 / 12
        new_monthly = original_monthly + extra_payment
        
        # Calculate months to payoff with extra payment
        balance = principal
        months = 0
        total_interest = 0
        
        while balance > 0 and months < original_months:
            interest = balance * monthly_rate
            principal_payment = new_monthly - interest
            
            if principal_payment >= balance:
                total_interest += balance * monthly_rate
                balance = 0
            else:
                total_interest += interest
                balance -= principal_payment
            
            months += 1
        
        return {
            "original_monthly": original_monthly,
            "original_interest": round(original_interest, 2),
            "original_months": original_months,
            "new_monthly": new_monthly,
            "new_interest": round(total_interest, 2),
            "new_months": months,
            "interest_saved": round(original_interest - total_interest, 2),
            "months_saved": original_months - months,
            "years_saved": round((original_months - months) / 12, 1)
        }