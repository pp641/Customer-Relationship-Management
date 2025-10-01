import  { useState, useEffect } from 'react';
import { PiggyBank, TrendingUp, Calendar, Percent } from 'lucide-react';

type DepositType = 'FD' | 'RD';
type CompoundingFrequency = 'monthly' | 'quarterly' | 'half-yearly' | 'yearly';

export default function FDRDCalculator() {
  const [depositType, setDepositType] = useState<DepositType>('FD');
  const [principalAmount, setPrincipalAmount] = useState(100000);
  const [monthlyDeposit, setMonthlyDeposit] = useState(5000);
  const [interestRate, setInterestRate] = useState(7.5);
  const [tenure, setTenure] = useState(12);
  const [tenureType, setTenureType] = useState<'months' | 'years'>('months');
  const [compoundingFrequency, setCompoundingFrequency] = useState<CompoundingFrequency>('quarterly');
  const [showCustomInput, setShowCustomInput] = useState(false);
  
  const [maturityAmount, setMaturityAmount] = useState(0);
  const [totalInterest, setTotalInterest] = useState(0);
  const [totalInvestment, setTotalInvestment] = useState(0);

  useEffect(() => {
    calculateReturns();
  }, [depositType, principalAmount, monthlyDeposit, interestRate, tenure, tenureType, compoundingFrequency]);

  const calculateReturns = () => {
    const tenureInMonths = tenureType === 'years' ? tenure * 12 : tenure;
    const tenureInYears = tenureInMonths / 12;
    const rate = interestRate / 100;

    if (depositType === 'FD') {
      // Fixed Deposit calculation
      let n = 4; // Default quarterly
      if (compoundingFrequency === 'monthly') n = 12;
      else if (compoundingFrequency === 'quarterly') n = 4;
      else if (compoundingFrequency === 'half-yearly') n = 2;
      else if (compoundingFrequency === 'yearly') n = 1;

      const maturity = principalAmount * Math.pow(1 + rate / n, n * tenureInYears);
      const interest = maturity - principalAmount;

      setMaturityAmount(maturity);
      setTotalInterest(interest);
      setTotalInvestment(principalAmount);
    } else {
      // Recurring Deposit calculation
      const monthlyRate = rate / 12;
      
      // RD formula: M = P × [(1 + i)^n - 1] / [1 - (1 + i)^(-1/3)]
      // Simplified: Using the standard RD formula
      let maturity = 0;
      for (let month = 1; month <= tenureInMonths; month++) {
        const remainingMonths = tenureInMonths - month + 1;
        maturity += monthlyDeposit * Math.pow(1 + monthlyRate, remainingMonths);
      }

      const totalInvested = monthlyDeposit * tenureInMonths;
      const interest = maturity - totalInvested;

      setMaturityAmount(maturity);
      setTotalInterest(interest);
      setTotalInvestment(totalInvested);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const handleReset = () => {
    setPrincipalAmount(100000);
    setMonthlyDeposit(5000);
    setInterestRate(7.5);
    setTenure(12);
    setTenureType('months');
    setCompoundingFrequency('quarterly');
    setDepositType('FD');
  };

  const investmentPercentage = (totalInvestment / maturityAmount) * 100 || 0;
  const interestPercentage = (totalInterest / maturityAmount) * 100 || 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-100 p-4 sm:p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-6 sm:p-8">
            <div className="flex items-center gap-3">
              <PiggyBank className="w-8 h-8 text-white" />
              <h1 className="text-2xl sm:text-3xl font-bold text-white">FD/RD Calculator</h1>
            </div>
            <p className="text-green-100 mt-2">Calculate returns on Fixed & Recurring Deposits</p>
          </div>

          <div className="p-6 sm:p-8">
            <div className="flex justify-between items-center mb-6">
              <button
                onClick={() => setShowCustomInput(!showCustomInput)}
                className="px-4 py-2 bg-emerald-100 text-emerald-700 rounded-lg font-medium hover:bg-emerald-200 transition text-sm"
              >
                {showCustomInput ? 'Use Sliders' : 'Custom Input'}
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition text-sm"
              >
                Clear
              </button>
            </div>

            <div className="grid lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Deposit Type
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => setDepositType('FD')}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition ${
                        depositType === 'FD'
                          ? 'border-green-600 bg-green-50 text-green-700'
                          : 'border-gray-200 hover:border-green-300'
                      }`}
                    >
                      <TrendingUp className="w-5 h-5" />
                      <span className="font-medium">Fixed Deposit</span>
                    </button>
                    <button
                      onClick={() => setDepositType('RD')}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition ${
                        depositType === 'RD'
                          ? 'border-green-600 bg-green-50 text-green-700'
                          : 'border-gray-200 hover:border-green-300'
                      }`}
                    >
                      <Calendar className="w-5 h-5" />
                      <span className="font-medium">Recurring Deposit</span>
                    </button>
                  </div>
                </div>

                {showCustomInput ? (
                  <div className="space-y-6">
                    {depositType === 'FD' ? (
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Principal Amount (₹)
                        </label>
                        <input
                          type="number"
                          value={principalAmount}
                          onChange={(e) => setPrincipalAmount(Number(e.target.value))}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none"
                          placeholder="Enter principal amount"
                        />
                      </div>
                    ) : (
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Monthly Deposit (₹)
                        </label>
                        <input
                          type="number"
                          value={monthlyDeposit}
                          onChange={(e) => setMonthlyDeposit(Number(e.target.value))}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none"
                          placeholder="Enter monthly deposit"
                        />
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Interest Rate (% per annum)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={interestRate}
                        onChange={(e) => setInterestRate(Number(e.target.value))}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none"
                        placeholder="Enter interest rate"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Tenure
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="number"
                          value={tenure}
                          onChange={(e) => setTenure(Number(e.target.value))}
                          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none"
                          placeholder="Enter tenure"
                        />
                        <select
                          value={tenureType}
                          onChange={(e) => setTenureType(e.target.value as 'months' | 'years')}
                          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none bg-white"
                        >
                          <option value="months">Months</option>
                          <option value="years">Years</option>
                        </select>
                      </div>
                    </div>

                    {depositType === 'FD' && (
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Compounding Frequency
                        </label>
                        <select
                          value={compoundingFrequency}
                          onChange={(e) => setCompoundingFrequency(e.target.value as CompoundingFrequency)}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none bg-white"
                        >
                          <option value="monthly">Monthly</option>
                          <option value="quarterly">Quarterly</option>
                          <option value="half-yearly">Half-Yearly</option>
                          <option value="yearly">Yearly</option>
                        </select>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-6">
                    {depositType === 'FD' ? (
                      <div>
                        <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                          <span>Principal Amount</span>
                          <span className="text-green-600">{formatCurrency(principalAmount)}</span>
                        </label>
                        <input
                          type="range"
                          min="10000"
                          max="10000000"
                          step="10000"
                          value={principalAmount}
                          onChange={(e) => setPrincipalAmount(Number(e.target.value))}
                          className="w-full h-2 bg-green-200 rounded-lg appearance-none cursor-pointer accent-green-600"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>₹10K</span>
                          <span>₹1Cr</span>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                          <span>Monthly Deposit</span>
                          <span className="text-green-600">{formatCurrency(monthlyDeposit)}</span>
                        </label>
                        <input
                          type="range"
                          min="500"
                          max="100000"
                          step="500"
                          value={monthlyDeposit}
                          onChange={(e) => setMonthlyDeposit(Number(e.target.value))}
                          className="w-full h-2 bg-green-200 rounded-lg appearance-none cursor-pointer accent-green-600"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>₹500</span>
                          <span>₹1L</span>
                        </div>
                      </div>
                    )}

                    <div>
                      <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                        <span>Interest Rate (per annum)</span>
                        <span className="text-green-600">{interestRate}%</span>
                      </label>
                      <input
                        type="range"
                        min="3"
                        max="12"
                        step="0.1"
                        value={interestRate}
                        onChange={(e) => setInterestRate(Number(e.target.value))}
                        className="w-full h-2 bg-green-200 rounded-lg appearance-none cursor-pointer accent-green-600"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>3%</span>
                        <span>12%</span>
                      </div>
                    </div>

                    <div>
                      <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                        <span>Tenure</span>
                        <span className="text-green-600">
                          {tenure} {tenureType}
                        </span>
                      </label>
                      <input
                        type="range"
                        min="1"
                        max={tenureType === 'years' ? 10 : 120}
                        step="1"
                        value={tenure}
                        onChange={(e) => setTenure(Number(e.target.value))}
                        className="w-full h-2 bg-green-200 rounded-lg appearance-none cursor-pointer accent-green-600"
                      />
                      <div className="flex justify-between items-center mt-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setTenureType('months');
                              if (tenure > 120) setTenure(120);
                            }}
                            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                              tenureType === 'months'
                                ? 'bg-green-600 text-white'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            Months
                          </button>
                          <button
                            onClick={() => {
                              setTenureType('years');
                              if (tenure > 10) setTenure(10);
                            }}
                            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                              tenureType === 'years'
                                ? 'bg-green-600 text-white'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            Years
                          </button>
                        </div>
                      </div>
                    </div>

                    {depositType === 'FD' && (
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Compounding Frequency
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                          {['monthly', 'quarterly', 'half-yearly', 'yearly'].map((freq) => (
                            <button
                              key={freq}
                              onClick={() => setCompoundingFrequency(freq as CompoundingFrequency)}
                              className={`p-2 rounded-lg text-sm font-medium transition ${
                                compoundingFrequency === freq
                                  ? 'bg-green-600 text-white'
                                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                              }`}
                            >
                              {freq.charAt(0).toUpperCase() + freq.slice(1).replace('-', ' ')}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="space-y-6">
                <div className="bg-gradient-to-br from-green-600 to-emerald-600 rounded-xl p-6 text-white">
                  <div className="flex items-center gap-2 mb-2">
                    <Percent className="w-5 h-5" />
                    <p className="text-sm font-medium opacity-90">Maturity Amount</p>
                  </div>
                  <p className="text-4xl font-bold">{formatCurrency(maturityAmount)}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
                    <p className="text-xs text-blue-600 font-medium mb-1">
                      {depositType === 'FD' ? 'Principal' : 'Total Invested'}
                    </p>
                    <p className="text-lg font-bold text-blue-700">{formatCurrency(totalInvestment)}</p>
                  </div>
                  <div className="bg-green-50 rounded-xl p-4 border border-green-200">
                    <p className="text-xs text-green-600 font-medium mb-1">Total Interest</p>
                    <p className="text-lg font-bold text-green-700">{formatCurrency(totalInterest)}</p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-xl p-4">
                  <p className="text-sm font-semibold text-gray-700 mb-3">Returns Breakdown</p>
                  <div className="flex h-6 rounded-lg overflow-hidden mb-3">
                    <div
                      className="bg-blue-500"
                      style={{ width: `${investmentPercentage}%` }}
                    ></div>
                    <div
                      className="bg-green-500"
                      style={{ width: `${interestPercentage}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-blue-500 rounded"></div>
                      <span className="text-gray-600">Investment {investmentPercentage.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded"></div>
                      <span className="text-gray-600">Interest {interestPercentage.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                  <h3 className="text-sm font-bold text-amber-900 mb-2">Investment Summary</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-amber-700">Deposit Type:</span>
                      <span className="font-semibold text-amber-900">
                        {depositType === 'FD' ? 'Fixed Deposit' : 'Recurring Deposit'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-amber-700">Duration:</span>
                      <span className="font-semibold text-amber-900">
                        {tenure} {tenureType}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-amber-700">Interest Rate:</span>
                      <span className="font-semibold text-amber-900">{interestRate}% p.a.</span>
                    </div>
                    {depositType === 'FD' && (
                      <div className="flex justify-between">
                        <span className="text-amber-700">Compounding:</span>
                        <span className="font-semibold text-amber-900 capitalize">
                          {compoundingFrequency.replace('-', ' ')}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-teal-50 rounded-xl p-4 border border-teal-200">
                  <div className="flex items-start gap-2">
                    <TrendingUp className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-bold text-teal-900 mb-1">Quick Tip</h3>
                      <p className="text-xs text-teal-700">
                        {depositType === 'FD' 
                          ? 'FDs with higher compounding frequency yield better returns. Choose monthly or quarterly for maximum benefits.'
                          : 'RDs help build financial discipline through regular savings. Ideal for goal-based investments like holidays or gadgets.'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}