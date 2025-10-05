import  { useState } from 'react';
import { CheckCircle2, XCircle, AlertCircle, TrendingUp, Home, Briefcase } from 'lucide-react';

interface EligibilityResult {
  isEligible: boolean;
  maxLoanAmount: number;
  recommendedEMI: number;
  eligibilityPercentage: number;
  factors: {
    income: string;
    creditScore: string;
    dti: string;
    age: string;
  };
  suggestions: string[];
}

export default function LoanEligibilityChecker() {
  const [monthlyIncome, setMonthlyIncome] = useState(50000);
  const [existingEMI, setExistingEMI] = useState(0);
  const [creditScore, setCreditScore] = useState(750);
  const [age, setAge] = useState(30);
  const [loanTenure, setLoanTenure] = useState(20);
  const [interestRate, setInterestRate] = useState(8.5);
  const [employmentType, setEmploymentType] = useState<'salaried' | 'self-employed'>('salaried');
  const [result, setResult] = useState<EligibilityResult | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [showCustomInput, setShowCustomInput] = useState(false);

  const calculateEligibility = () => {
    const foir = employmentType === 'salaried' ? 0.5 : 0.4;
    const availableIncome = monthlyIncome - existingEMI;
    const maxEMI = availableIncome * foir;
    
    const ratePerMonth = interestRate / 12 / 100;
    const tenureInMonths = loanTenure * 12;
    const maxLoan = (maxEMI * (Math.pow(1 + ratePerMonth, tenureInMonths) - 1)) / 
                    (ratePerMonth * Math.pow(1 + ratePerMonth, tenureInMonths));

    const dti = (existingEMI / monthlyIncome) * 100;

    let eligibilityScore = 100;
    const factors = {
      income: 'Good',
      creditScore: 'Good',
      dti: 'Good',
      age: 'Good'
    };
    const suggestions: string[] = [];

    if (creditScore < 650) {
      eligibilityScore -= 40;
      factors.creditScore = 'Poor';
      suggestions.push('Improve your credit score by paying bills on time and reducing credit utilization');
    } else if (creditScore < 750) {
      eligibilityScore -= 20;
      factors.creditScore = 'Fair';
      suggestions.push('A credit score above 750 will help you get better interest rates');
    } else {
      factors.creditScore = 'Excellent';
    }

    if (dti > 50) {
      eligibilityScore -= 30;
      factors.dti = 'High';
      suggestions.push('Reduce existing loan obligations to improve debt-to-income ratio');
    } else if (dti > 40) {
      eligibilityScore -= 15;
      factors.dti = 'Moderate';
      suggestions.push('Try to keep your total EMI below 40% of monthly income');
    } else {
      factors.dti = 'Low';
    }

    if (age < 21 || age > 60) {
      eligibilityScore -= 20;
      factors.age = 'Outside optimal range';
      suggestions.push('Age is outside the optimal range for maximum loan tenure');
    } else if (age > 55) {
      eligibilityScore -= 10;
      factors.age = 'Fair';
    } else {
      factors.age = 'Optimal';
    }

    if (monthlyIncome < 25000) {
      eligibilityScore -= 25;
      factors.income = 'Low';
      suggestions.push('Minimum income requirement for most lenders is ₹25,000 per month');
    } else if (monthlyIncome < 50000) {
      eligibilityScore -= 10;
      factors.income = 'Moderate';
    } else {
      factors.income = 'Strong';
    }

    const isEligible = eligibilityScore >= 50 && creditScore >= 650 && monthlyIncome >= 25000;

    if (suggestions.length === 0) {
      suggestions.push('Your profile is strong! You may qualify for premium interest rates');
      suggestions.push('Consider making a larger down payment to reduce loan amount');
    }

    setResult({
      isEligible,
      maxLoanAmount: maxLoan,
      recommendedEMI: maxEMI,
      eligibilityPercentage: Math.max(0, eligibilityScore),
      factors,
      suggestions
    });
    setShowResult(true);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const handleReset = () => {
    setMonthlyIncome(50000);
    setExistingEMI(0);
    setCreditScore(750);
    setAge(30);
    setLoanTenure(20);
    setInterestRate(8.5);
    setEmploymentType('salaried');
    setShowResult(false);
    setResult(null);
    setShowCustomInput(false);
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 75) return 'bg-green-500';
    if (score >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 p-4 sm:p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="bg-gradient-to-r from-purple-600 to-indigo-600 p-6 sm:p-8">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-white" />
              <h1 className="text-2xl sm:text-3xl font-bold text-white">Loan Eligibility Checker</h1>
            </div>
            <p className="text-purple-100 mt-2">Check your loan eligibility and get personalized recommendations</p>
          </div>

          <div className="p-6 sm:p-8">
            {!showResult ? (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <button
                    onClick={() => setShowCustomInput(!showCustomInput)}
                    className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg font-medium hover:bg-indigo-200 transition text-sm"
                  >
                    {showCustomInput ? 'Use Sliders' : 'Custom Input'}
                  </button>
                </div>

                {showCustomInput ? (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Employment Type
                      </label>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          onClick={() => setEmploymentType('salaried')}
                          className={`flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition ${
                            employmentType === 'salaried'
                              ? 'border-purple-600 bg-purple-50 text-purple-700'
                              : 'border-gray-200 hover:border-purple-300'
                          }`}
                        >
                          <Briefcase className="w-5 h-5" />
                          <span className="font-medium">Salaried</span>
                        </button>
                        <button
                          onClick={() => setEmploymentType('self-employed')}
                          className={`flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition ${
                            employmentType === 'self-employed'
                              ? 'border-purple-600 bg-purple-50 text-purple-700'
                              : 'border-gray-200 hover:border-purple-300'
                          }`}
                        >
                          <Home className="w-5 h-5" />
                          <span className="font-medium">Self-Employed</span>
                        </button>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Monthly Income (₹)
                        </label>
                        <input
                          type="number"
                          value={monthlyIncome}
                          onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                          placeholder="Enter monthly income"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Existing Monthly EMI (₹)
                        </label>
                        <input
                          type="number"
                          value={existingEMI}
                          onChange={(e) => setExistingEMI(Number(e.target.value))}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                          placeholder="Enter existing EMI"
                        />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Credit Score
                        </label>
                        <input
                          type="number"
                          min="300"
                          max="900"
                          value={creditScore}
                          onChange={(e) => setCreditScore(Number(e.target.value))}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                          placeholder="Enter credit score"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Your Age (years)
                        </label>
                        <input
                          type="number"
                          min="18"
                          max="65"
                          value={age}
                          onChange={(e) => setAge(Number(e.target.value))}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                          placeholder="Enter your age"
                        />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Loan Tenure (years)
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="30"
                          value={loanTenure}
                          onChange={(e) => setLoanTenure(Number(e.target.value))}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                          placeholder="Enter loan tenure"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Interest Rate (% per annum)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          min="6"
                          max="15"
                          value={interestRate}
                          onChange={(e) => setInterestRate(Number(e.target.value))}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                          placeholder="Enter interest rate"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Employment Type
                        </label>
                        <div className="grid grid-cols-2 gap-3">
                          <button
                            onClick={() => setEmploymentType('salaried')}
                            className={`flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition ${
                              employmentType === 'salaried'
                                ? 'border-purple-600 bg-purple-50 text-purple-700'
                                : 'border-gray-200 hover:border-purple-300'
                            }`}
                          >
                            <Briefcase className="w-5 h-5" />
                            <span className="font-medium">Salaried</span>
                          </button>
                          <button
                            onClick={() => setEmploymentType('self-employed')}
                            className={`flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition ${
                              employmentType === 'self-employed'
                                ? 'border-purple-600 bg-purple-50 text-purple-700'
                                : 'border-gray-200 hover:border-purple-300'
                            }`}
                          >
                            <Home className="w-5 h-5" />
                            <span className="font-medium">Self-Employed</span>
                          </button>
                        </div>
                      </div>

                      <div>
                        <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                          <span>Monthly Income</span>
                          <span className="text-purple-600">{formatCurrency(monthlyIncome)}</span>
                        </label>
                        <input
                          type="range"
                          min="10000"
                          max="500000"
                          step="5000"
                          value={monthlyIncome}
                          onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                          className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>₹10K</span>
                          <span>₹5L</span>
                        </div>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                          <span>Existing Monthly EMI</span>
                          <span className="text-purple-600">{formatCurrency(existingEMI)}</span>
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="100000"
                          step="1000"
                          value={existingEMI}
                          onChange={(e) => setExistingEMI(Number(e.target.value))}
                          className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>₹0</span>
                          <span>₹1L</span>
                        </div>
                      </div>

                      <div>
                        <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                          <span>Credit Score</span>
                          <span className={`${creditScore >= 750 ? 'text-green-600' : creditScore >= 650 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {creditScore}
                          </span>
                        </label>
                        <input
                          type="range"
                          min="300"
                          max="900"
                          step="10"
                          value={creditScore}
                          onChange={(e) => setCreditScore(Number(e.target.value))}
                          className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>300</span>
                          <span>900</span>
                        </div>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                          <span>Your Age</span>
                          <span className="text-purple-600">{age} years</span>
                        </label>
                        <input
                          type="range"
                          min="18"
                          max="65"
                          step="1"
                          value={age}
                          onChange={(e) => setAge(Number(e.target.value))}
                          className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>18</span>
                          <span>65</span>
                        </div>
                      </div>

                      <div>
                        <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                          <span>Loan Tenure</span>
                          <span className="text-purple-600">{loanTenure} years</span>
                        </label>
                        <input
                          type="range"
                          min="1"
                          max="30"
                          step="1"
                          value={loanTenure}
                          onChange={(e) => setLoanTenure(Number(e.target.value))}
                          className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>1 year</span>
                          <span>30 years</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                        <span>Expected Interest Rate (per annum)</span>
                        <span className="text-purple-600">{interestRate}%</span>
                      </label>
                      <input
                        type="range"
                        min="6"
                        max="15"
                        step="0.1"
                        value={interestRate}
                        onChange={(e) => setInterestRate(Number(e.target.value))}
                        className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>6%</span>
                        <span>15%</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={calculateEligibility}
                    className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-indigo-700 transition shadow-lg"
                  >
                    Check Eligibility
                  </button>
                  <button
                    onClick={handleReset}
                    className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition"
                  >
                    Reset
                  </button>
                </div>
              </div>
            ) : result && (
              <div className="space-y-6">
                <div className={`rounded-xl p-6 ${result.isEligible ? 'bg-green-50 border-2 border-green-200' : 'bg-red-50 border-2 border-red-200'}`}>
                  <div className="flex items-center gap-3 mb-4">
                    {result.isEligible ? (
                      <CheckCircle2 className="w-8 h-8 text-green-600" />
                    ) : (
                      <XCircle className="w-8 h-8 text-red-600" />
                    )}
                    <div>
                      <h2 className={`text-2xl font-bold ${result.isEligible ? 'text-green-700' : 'text-red-700'}`}>
                        {result.isEligible ? 'Congratulations!' : 'Not Eligible'}
                      </h2>
                      <p className={`text-sm ${result.isEligible ? 'text-green-600' : 'text-red-600'}`}>
                        {result.isEligible 
                          ? 'You are eligible for a home loan' 
                          : 'You may need to improve your profile'}
                      </p>
                    </div>
                  </div>

                  <div className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">Eligibility Score</span>
                      <span className={`text-lg font-bold ${getScoreColor(result.eligibilityPercentage)}`}>
                        {result.eligibilityPercentage.toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                      <div
                        className={`h-full ${getScoreBgColor(result.eligibilityPercentage)} transition-all duration-1000`}
                        style={{ width: `${result.eligibilityPercentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
                    <p className="text-sm opacity-90 mb-1">Maximum Loan Amount</p>
                    <p className="text-3xl font-bold">{formatCurrency(result.maxLoanAmount)}</p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-xl p-6 text-white">
                    <p className="text-sm opacity-90 mb-1">Recommended EMI</p>
                    <p className="text-3xl font-bold">{formatCurrency(result.recommendedEMI)}</p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="text-lg font-bold text-gray-800 mb-4">Eligibility Factors</h3>
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <span className="text-sm text-gray-600">Income Level</span>
                      <span className="text-sm font-semibold text-gray-800">{result.factors.income}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <span className="text-sm text-gray-600">Credit Score</span>
                      <span className="text-sm font-semibold text-gray-800">{result.factors.creditScore}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <span className="text-sm text-gray-600">Debt-to-Income</span>
                      <span className="text-sm font-semibold text-gray-800">{result.factors.dti}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <span className="text-sm text-gray-600">Age Factor</span>
                      <span className="text-sm font-semibold text-gray-800">{result.factors.age}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                    <div>
                      <h3 className="text-lg font-bold text-blue-900 mb-3">Recommendations</h3>
                      <ul className="space-y-2">
                        {result.suggestions.map((suggestion, index) => (
                          <li key={index} className="text-sm text-blue-800 flex items-start gap-2">
                            <span className="text-blue-600 mt-1">•</span>
                            <span>{suggestion}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setShowResult(false)}
                    className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-indigo-700 transition shadow-lg"
                  >
                    Check Again
                  </button>
                  <button
                    onClick={handleReset}
                    className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition"
                  >
                    Reset
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}