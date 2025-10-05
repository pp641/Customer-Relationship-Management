# routes/financial.py - Financial Services API Router
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from services.financial_service import FinancialService

router = APIRouter(
    prefix="/api/financial",
    tags=["financial-services"]
)

# Initialize service
financial_service = FinancialService()

# Request/Response Models
class LoanCalculationRequest(BaseModel):
    principal: float = Field(..., gt=0, description="Loan amount")
    annual_rate: float = Field(..., gt=0, le=100, description="Annual interest rate (%)")
    years: int = Field(..., gt=0, le=30, description="Loan term in years")

class LoanCalculationResponse(BaseModel):
    monthly_payment: float
    total_payment: float
    total_interest: float
    principal: float
    rate: float
    term_years: int
    amortization_schedule: Optional[List[Dict]] = None

class EligibilityRequest(BaseModel):
    income: float = Field(..., gt=0, description="Annual income")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score")
    existing_debt: float = Field(..., ge=0, description="Existing debt amount")
    employment_years: Optional[int] = Field(None, ge=0, description="Years in current employment")

class EligibilityResponse(BaseModel):
    eligibility: str
    max_loan_amount: float
    credit_score: int
    rate_adjustment: float
    approved: bool
    recommendation: str

class LoanComparisonRequest(BaseModel):
    amount: float = Field(..., gt=0)
    term: int = Field(..., gt=0, le=30)
    credit_score: Optional[int] = Field(None, ge=300, le=850)

class LoanProduct(BaseModel):
    product_type: str
    product_name: str
    interest_rate: str
    monthly_payment: float
    total_interest: float
    eligibility_score: Optional[str] = None

class LoanComparisonResponse(BaseModel):
    comparisons: List[LoanProduct]
    best_option: Optional[str] = None
    total_products: int

# Endpoints
@router.post("/calculate", response_model=LoanCalculationResponse)
async def calculate_loan_payment(request: LoanCalculationRequest, include_schedule: bool = False):
    """
    Calculate loan payment details including EMI, total payment, and interest
    
    Example:
    ```json
    {
        "principal": 50000,
        "annual_rate": 8.5,
        "years": 5
    }
    ```
    """
    try:
        result = financial_service.calculate_loan_payment(
            principal=request.principal,
            annual_rate=request.annual_rate,
            years=request.years,
            include_schedule=include_schedule
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

@router.post("/eligibility", response_model=EligibilityResponse)
async def check_eligibility(request: EligibilityRequest):
    """
    Check loan eligibility based on financial profile
    
    Example:
    ```json
    {
        "income": 60000,
        "credit_score": 720,
        "existing_debt": 15000,
        "employment_years": 3
    }
    ```
    """
    try:
        result = financial_service.check_eligibility(
            income=request.income,
            credit_score=request.credit_score,
            existing_debt=request.existing_debt,
            employment_years=request.employment_years
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eligibility check error: {str(e)}")

@router.post("/compare", response_model=LoanComparisonResponse)
async def compare_loans(request: LoanComparisonRequest):
    """
    Compare different loan products for given amount and term
    
    Example:
    ```json
    {
        "amount": 50000,
        "term": 5,
        "credit_score": 720
    }
    ```
    """
    try:
        result = financial_service.compare_loans(
            amount=request.amount,
            term=request.term,
            credit_score=request.credit_score
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")

@router.get("/products")
async def get_loan_products(loan_type: Optional[str] = None):
    """
    Get available loan products
    
    Query Parameters:
    - loan_type: Filter by type (personal, home, auto, business)
    """
    try:
        products = financial_service.get_loan_products(loan_type)
        return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.get("/rates")
async def get_current_rates():
    """
    Get current interest rates for all loan products
    """
    try:
        rates = financial_service.get_current_rates()
        return {"rates": rates, "last_updated": rates.get("updated_at")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rates: {str(e)}")

@router.post("/affordability")
async def calculate_affordability(
    income: float = Query(..., gt=0),
    monthly_expenses: float = Query(..., ge=0),
    desired_term: int = Query(..., gt=0, le=30)
):
    """
    Calculate maximum affordable loan amount
    """
    try:
        result = financial_service.calculate_affordability(
            income=income,
            monthly_expenses=monthly_expenses,
            desired_term=desired_term
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Affordability calculation error: {str(e)}")

@router.post("/early-payoff")
async def calculate_early_payoff(
    principal: float = Query(..., gt=0),
    annual_rate: float = Query(..., gt=0),
    years: int = Query(..., gt=0),
    extra_payment: float = Query(..., gt=0)
):
    """
    Calculate savings from making extra payments
    """
    try:
        result = financial_service.calculate_early_payoff(
            principal=principal,
            annual_rate=annual_rate,
            years=years,
            extra_payment=extra_payment
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Early payoff calculation error: {str(e)}")