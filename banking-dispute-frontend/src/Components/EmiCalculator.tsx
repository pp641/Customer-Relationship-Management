import  { useState, useEffect } from 'react';
import { Calculator, IndianRupee } from 'lucide-react';

export default function EMICalculator() {
  const [loanAmount, setLoanAmount] = useState(500000);
  const [interestRate, setInterestRate] = useState(8.5);
  const [loanTenure, setLoanTenure] = useState(12);
  const [tenureType, setTenureType] = useState<'months' | 'years'>('months');
  const [emi, setEmi] = useState(0);
  const [totalInterest, setTotalInterest] = useState(0);
  const [totalAmount, setTotalAmount] = useState(0);
  const [showCustomInput, setShowCustomInput] = useState(false);

  useEffect(() => {
    calculateEMI();
  }, [loanAmount, interestRate, loanTenure, tenureType]);

  const calculateEMI = () => {
    const principal = loanAmount;
    const ratePerMonth = interestRate / 12 / 100;
    const tenureInMonths = tenureType === 'years' ? loanTenure * 12 : loanTenure;

    if (principal > 0 && ratePerMonth > 0 && tenureInMonths > 0) {
      const emiValue =
        (principal * ratePerMonth * Math.pow(1 + ratePerMonth, tenureInMonths)) /
        (Math.pow(1 + ratePerMonth, tenureInMonths) - 1);

      const totalPayment = emiValue * tenureInMonths;
      const interestPayment = totalPayment - principal;

      setEmi(emiValue);
      setTotalInterest(interestPayment);
      setTotalAmount(totalPayment);
    } else {
      setEmi(0);
      setTotalInterest(0);
      setTotalAmount(0);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const handleClear = () => {
    setLoanAmount(500000);
    setInterestRate(8.5);
    setLoanTenure(12);
    setTenureType('months');
  };

  const handleCalculate = () => {
    calculateEMI();
    setShowCustomInput(false);
  };

  const principalPercentage = (loanAmount / totalAmount) * 100 || 0;
  const interestPercentage = (totalInterest / totalAmount) * 100 || 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4 sm:p-8">
      <div className="max-w-5xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 sm:p-8">
            <div className="flex items-center gap-3">
              <Calculator className="w-8 h-8 text-white" />
              <h1 className="text-2xl sm:text-3xl font-bold text-white">EMI Calculator</h1>
            </div>
            <p className="text-blue-100 mt-2">Calculate your loan EMI instantly</p>
          </div>

          <div className="p-6 sm:p-8">
            <div className="flex justify-between items-center mb-6">
              <button
                onClick={() => setShowCustomInput(!showCustomInput)}
                className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg font-medium hover:bg-indigo-200 transition text-sm"
              >
                {showCustomInput ? 'Use Sliders' : 'Custom Input'}
              </button>
              <button
                onClick={handleClear}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition text-sm"
              >
                Clear
              </button>
            </div>

            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-6">
                {showCustomInput ? (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Loan Amount (₹)
                      </label>
                      <input
                        type="number"
                        value={loanAmount}
                        onChange={(e) => setLoanAmount(Number(e.target.value))}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="Enter loan amount"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Interest Rate (% per annum)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={interestRate}
                        onChange={(e) => setInterestRate(Number(e.target.value))}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="Enter interest rate"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Loan Tenure
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="number"
                          value={loanTenure}
                          onChange={(e) => setLoanTenure(Number(e.target.value))}
                          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                          placeholder="Enter tenure"
                        />
                        <select
                          value={tenureType}
                          onChange={(e) => setTenureType(e.target.value as 'months' | 'years')}
                          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white"
                        >
                          <option value="months">Months</option>
                          <option value="years">Years</option>
                        </select>
                      </div>
                    </div>

                    <button
                      onClick={handleCalculate}
                      className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition shadow-lg"
                    >
                      Calculate EMI
                    </button>
                  </div>
                ) : (
                  <>
                    <div>
                      <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                        <span>Loan Amount</span>
                        <span className="text-blue-600">{formatCurrency(loanAmount)}</span>
                      </label>
                      <input
                        type="range"
                        min="10000"
                        max="10000000"
                        step="10000"
                        value={loanAmount}
                        onChange={(e) => setLoanAmount(Number(e.target.value))}
                        className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>₹10K</span>
                        <span>₹1Cr</span>
                      </div>
                    </div>

                    <div>
                      <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                        <span>Interest Rate (per annum)</span>
                        <span className="text-blue-600">{interestRate}%</span>
                      </label>
                      <input
                        type="range"
                        min="1"
                        max="30"
                        step="0.1"
                        value={interestRate}
                        onChange={(e) => setInterestRate(Number(e.target.value))}
                        className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>1%</span>
                        <span>30%</span>
                      </div>
                    </div>

                    <div>
                      <label className="flex items-center justify-between text-sm font-semibold text-gray-700 mb-3">
                        <span>Loan Tenure</span>
                        <span className="text-blue-600">
                          {loanTenure} {tenureType}
                        </span>
                      </label>
                      <input
                        type="range"
                        min="1"
                        max={tenureType === 'years' ? 30 : 360}
                        step="1"
                        value={loanTenure}
                        onChange={(e) => setLoanTenure(Number(e.target.value))}
                        className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                      />
                      <div className="flex justify-between items-center mt-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setTenureType('months');
                              if (loanTenure > 360) setLoanTenure(360);
                            }}
                            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                              tenureType === 'months'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            Months
                          </button>
                          <button
                            onClick={() => {
                              setTenureType('years');
                              if (loanTenure > 30) setLoanTenure(30);
                            }}
                            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                              tenureType === 'years'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            Years
                          </button>
                        </div>
                        <span className="text-xs text-gray-500">
                          Max: {tenureType === 'years' ? '30 years' : '360 months'}
                        </span>
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="space-y-6">
                <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
                  <div className="flex items-center gap-2 mb-2">
                    <IndianRupee className="w-5 h-5" />
                    <p className="text-sm font-medium opacity-90">Monthly EMI</p>
                  </div>
                  <p className="text-4xl font-bold">{formatCurrency(emi)}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-green-50 rounded-xl p-4 border border-green-200">
                    <p className="text-xs text-green-600 font-medium mb-1">Principal Amount</p>
                    <p className="text-lg font-bold text-green-700">{formatCurrency(loanAmount)}</p>
                  </div>
                  <div className="bg-orange-50 rounded-xl p-4 border border-orange-200">
                    <p className="text-xs text-orange-600 font-medium mb-1">Total Interest</p>
                    <p className="text-lg font-bold text-orange-700">{formatCurrency(totalInterest)}</p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                  <p className="text-sm text-gray-600 font-medium mb-1">Total Amount Payable</p>
                  <p className="text-2xl font-bold text-gray-800">{formatCurrency(totalAmount)}</p>
                </div>

                <div className="bg-gray-50 rounded-xl p-4">
                  <p className="text-sm font-semibold text-gray-700 mb-3">Payment Breakdown</p>
                  <div className="flex h-6 rounded-lg overflow-hidden mb-3">
                    <div
                      className="bg-green-500"
                      style={{ width: `${principalPercentage}%` }}
                    ></div>
                    <div
                      className="bg-orange-500"
                      style={{ width: `${interestPercentage}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded"></div>
                      <span className="text-gray-600">Principal {principalPercentage.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-orange-500 rounded"></div>
                      <span className="text-gray-600">Interest {interestPercentage.toFixed(1)}%</span>
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