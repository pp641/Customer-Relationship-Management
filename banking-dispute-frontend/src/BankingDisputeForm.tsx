import React, { useState, useEffect } from 'react';
import {   Clock, FileText, Download,  ArrowRight } from 'lucide-react';
import "./index.css"
import type { DisputeData, GuidanceStep  } from './types/types';
import  { disputeTypes , baseSteps, TABS , banks, EVIDENCE_CHECKLIST } from './types/types';
import FooterComponent from './Components/Footer';
import Header from './Components/Header';




const BankingDisputePlatform: React.FC = () => {
  const [disputes, setDisputes] = useState<DisputeData[]>([]);
  const [formData, setFormData] = useState({
    type: '',
    amount: '',
    date: '',
    description: '',
    bank: '',
    cardLast4: '',
    transactionId: ''
  });
  const [guidance, setGuidance] = useState<GuidanceStep[]>([]);
  const [activeTab, setActiveTab] = useState('report');



 
  useEffect(() => {
    // Load existing disputes from localStorage
    const savedDisputes = localStorage.getItem('banking-disputes');
    if (savedDisputes) {
      setDisputes(JSON.parse(savedDisputes));
    }
  }, []);

  const generateGuidance = (type: string): GuidanceStep[] => {


    const specificSteps: { [key: string]: GuidanceStep[] } = {
      'Double Debit / Duplicate Charge': [
        ...baseSteps,
        {
          step: 4,
          title: "Request Transaction Reversal",
          description: "Ask for immediate reversal of duplicate charge",
          template: "reversal_request"
        },
        {
          step: 5,
          title: "Follow Up",
          description: "Bank should resolve within 7-10 working days",
          action: "Track complaint reference number"
        }
      ],
      'Unauthorized Transaction': [
        ...baseSteps,
        {
          step: 4,
          title: "Block Card Immediately",
          description: "Request immediate card blocking to prevent further fraud",
          action: "Call bank hotline to block card"
        },
        {
          step: 5,
          title: "File Police Complaint",
          description: "For amounts above ₹25,000, file FIR",
          template: "police_complaint"
        },
        {
          step: 6,
          title: "Chargeback Request",
          description: "Request chargeback from bank",
          template: "chargeback_request"
        }
      ],
      'Missing Refund': [
        ...baseSteps,
        {
          step: 4,
          title: "Contact Merchant",
          description: "First contact the merchant for refund status",
          template: "merchant_query"
        },
        {
          step: 5,
          title: "Bank Refund Request",
          description: "If merchant doesn't respond in 7 days",
          template: "refund_request"
        }
      ]
    };

    return specificSteps[type] || baseSteps;
  };

  const handleSubmit = () => {
    // Basic validation
    if (!formData.type || !formData.amount || !formData.date || !formData.description) {
      alert('Please fill in all required fields');
      return;
    }
    
    const newDispute: DisputeData = {
      id: Date.now().toString(),
      type: formData.type,
      amount: parseFloat(formData.amount),
      date: formData.date,
      description: formData.description,
      status: 'submitted',
      priority: parseFloat(formData.amount) > 50000 ? 'high' : parseFloat(formData.amount) > 10000 ? 'medium' : 'low',
      bank: formData.bank,
      cardLast4: formData.cardLast4,
      createdAt: new Date().toISOString()
    };

    const updatedDisputes = [...disputes, newDispute];
    setDisputes(updatedDisputes);
    localStorage.setItem('banking-disputes', JSON.stringify(updatedDisputes));
    
    setGuidance(generateGuidance(formData.type));
    setActiveTab('guidance');
    
    // Reset form
    setFormData({
      type: '', amount: '', date: '', description: '',
      bank: '', cardLast4: '', transactionId: ''
    });
  };

  const getTemplate = (templateType: string, disputeType: string) => {
    const templates: { [key: string]: string } = {
      formal_complaint: `Subject: Formal Complaint - ${disputeType}

Dear Sir/Madam,

I am writing to file a formal complaint regarding a ${disputeType.toLowerCase()} on my account.

Transaction Details:
- Date: ${formData.date}
- Amount: ₹${formData.amount}
- Card ending: xxxx${formData.cardLast4}
- Description: ${formData.description}

I request immediate investigation and resolution of this matter within the stipulated timeframe as per RBI guidelines.

Please provide a complaint reference number for tracking.

Regards,
[Your Name]
[Account Number]
[Contact Details]`,

      chargeback_request: `Subject: Chargeback Request - Unauthorized Transaction

Dear Chargeback Team,

I request a chargeback for the following unauthorized transaction:

Transaction Details:
- Date: ${formData.date}
- Amount: ₹${formData.amount}
- Merchant: [Merchant Name]
- Card: xxxx${formData.cardLast4}

Reason: Unauthorized transaction - I did not authorize this payment.

Evidence Attached:
- Bank statement
- Card blocking confirmation
- Police complaint (if applicable)

Please process this chargeback under Visa/Mastercard dispute resolution.

Thank you,
[Your Name]`,

      reversal_request: `Subject: Request for Transaction Reversal - Duplicate Charge

Dear Team,

I request immediate reversal of a duplicate charge on my account:

Original Transaction: ₹${formData.amount} on ${formData.date}
Duplicate Transaction: ₹${formData.amount} on ${formData.date}

Total Amount to be Reversed: ₹${formData.amount}

This appears to be a system error resulting in double billing.

Please reverse the duplicate amount immediately.

Regards,
[Your Name]`
    };

    return templates[templateType] || '';
  };

  const StatusBadge = ({ status }: { status: string }) => {
    const colors = {
      submitted: 'bg-blue-100 text-blue-800',
      under_review: 'bg-yellow-100 text-yellow-800',
      resolved: 'bg-green-100 text-green-800',
      escalated: 'bg-red-100 text-red-800'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status as keyof typeof colors]}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const PriorityBadge = ({ priority }: { priority: string }) => {
    const colors = {
      low: 'bg-gray-100 text-gray-800',
      medium: 'bg-orange-100 text-orange-800',
      high: 'bg-red-100 text-red-800'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[priority as keyof typeof colors]}`}>
        {priority.toUpperCase()}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header/>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <nav className="flex space-x-8">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-blue-50'
                }`}
              >
                <tab.icon className="h-5 w-5 mr-2" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {activeTab === 'report' && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Report Banking Issue</h2>
            
            <div className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Issue Type *
                  </label>
                  <select
                    required
                    value={formData.type}
                    onChange={(e) => setFormData({...formData, type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select Issue Type</option>
                    {disputeTypes.map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bank *
                  </label>
                  <select
                    required
                    value={formData.bank}
                    onChange={(e) => setFormData({...formData, bank: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select Bank</option>
                    {banks.map((bank) => (
                      <option key={bank} value={bank}>{bank}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Transaction Amount (₹) *
                  </label>
                  <input
                    type="number"
                    required
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => setFormData({...formData, amount: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter amount"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Transaction Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.date}
                    onChange={(e) => setFormData({...formData, date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Card Last 4 Digits
                  </label>
                  <input
                    type="text"
                    maxLength={4}
                    value={formData.cardLast4}
                    onChange={(e) => setFormData({...formData, cardLast4: e.target.value.replace(/\D/g, '')})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    placeholder="1234"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Transaction ID (if available)
                  </label>
                  <input
                    type="text"
                    value={formData.transactionId}
                    onChange={(e) => setFormData({...formData, transactionId: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Transaction reference number"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description *
                </label>
                <textarea
                  required
                  rows={4}
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Describe the issue in detail..."
                />
              </div>

              <button
                onClick={handleSubmit}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center cursor-pointer"
              >
                Submit Report & Get Guidance
                <ArrowRight className="h-5 w-5 ml-2" />
              </button>
            </div>
          </div>
        )}

        {activeTab === 'guidance' && (
          <div className="space-y-6">
            {guidance.length > 0 ? (
              <div className="bg-white rounded-xl shadow-lg p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Step-by-Step Guidance</h2>
                
                <div className="space-y-6">
                  {guidance.map((step) => (
                    <div key={step.step} className="border border-gray-200 rounded-lg p-6">
                      <div className="flex items-start space-x-4">
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                            {step.step}
                          </div>
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            {step.title}
                          </h3>
                          <p className="text-gray-600 mb-3">{step.description}</p>
                          
                          {step.action && (
                            <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-3">
                              <p className="text-blue-800 font-medium">{step.action}</p>
                            </div>
                          )}
                          
                          {step.template && (
                            <div className="mt-4">
                              <h4 className="font-medium text-gray-900 mb-2">Email Template:</h4>
                              <div className="bg-gray-50 border rounded-lg p-4">
                                <pre className="text-sm text-gray-800 whitespace-pre-wrap">
                                  {getTemplate(step.template, formData.type)}
                                </pre>
                              </div>
                              <button className="mt-2 text-blue-600 hover:text-blue-700 font-medium flex items-center">
                                <Download className="h-4 w-4 mr-1" />
                                Copy Template
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-lg p-8 text-center">
                <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Guidance</h3>
                <p className="text-gray-600">Report an issue to get step-by-step guidance and templates.</p>
              </div>
            )}

            {/* Evidence Checklist */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Evidence Checklist</h3>
              <div className="grid md:grid-cols-2 gap-4">
                {EVIDENCE_CHECKLIST.map((item, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <input type="checkbox" className="rounded text-blue-600" />
                    <label className="text-gray-700">{item}</label>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Track Disputes Tab */}
        {activeTab === 'track' && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Track Your Disputes</h2>
            
            {disputes.length > 0 ? (
              <div className="space-y-4">
                {disputes.map((dispute) => (
                  <div key={dispute.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">{dispute.type}</h3>
                          <StatusBadge status={dispute.status} />
                          <PriorityBadge priority={dispute.priority} />
                        </div>
                        <div className="grid md:grid-cols-3 gap-4 text-sm text-gray-600">
                          <div>
                            <span className="font-medium">Amount:</span> ₹{dispute.amount.toLocaleString()}
                          </div>
                          <div>
                            <span className="font-medium">Bank:</span> {dispute.bank}
                          </div>
                          <div>
                            <span className="font-medium">Date:</span> {new Date(dispute.date).toLocaleDateString()}
                          </div>
                        </div>
                        <p className="text-gray-700 mt-2">{dispute.description}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500">
                          Reported: {new Date(dispute.createdAt).toLocaleDateString()}
                        </div>
                        <button className="mt-2 text-blue-600 hover:text-blue-700 font-medium">
                          View Details
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Clock className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Disputes Yet</h3>
                <p className="text-gray-600">Your reported issues will appear here for tracking.</p>
              </div>
            )}
          </div>
        )}
      </div>
      <FooterComponent/>
    </div>
  );
};

export default BankingDisputePlatform;