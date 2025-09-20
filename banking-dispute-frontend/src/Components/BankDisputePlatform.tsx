import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Clock, FileText, Phone, Mail, Download, ArrowRight, Shield } from 'lucide-react';
import "./index.css";
import type { 
  DisputeData, 
  GuidanceStep, 
  FormData, 
  TabType, 
  StatusType, 
  PriorityType 
} from './types';
import { 
  DISPUTE_TYPES,
  BANKS,
  TABS,
  EVIDENCE_CHECKLIST,
  STATUS_COLORS,
  PRIORITY_COLORS,
  calculatePriority,
  generateGuidance,
  getTemplate,
  saveDisputes,
  loadDisputes
} from './utils';

// Badge Components
const StatusBadge: React.FC<{ status: StatusType }> = ({ status }) => (
  <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[status]}`}>
    {status.replace('_', ' ').toUpperCase()}
  </span>
);

const PriorityBadge: React.FC<{ priority: PriorityType }> = ({ priority }) => (
  <span className={`px-2 py-1 rounded-full text-xs font-medium ${PRIORITY_COLORS[priority]}`}>
    {priority.toUpperCase()}
  </span>
);

// Form Component
const ReportForm: React.FC<{
  formData: FormData;
  setFormData: (data: FormData) => void;
  onSubmit: () => void;
}> = ({ formData, setFormData, onSubmit }) => (
  <div className="bg-white rounded-xl shadow-lg p-8">
    <h2 className="text-2xl font-bold text-gray-900 mb-6">Report Banking Issue</h2>
    
    <div className="space-y-6">
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Issue Type *</label>
          <select
            required
            value={formData.type}
            onChange={(e) => setFormData({...formData, type: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select Issue Type</option>
            {DISPUTE_TYPES.map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Bank *</label>
          <select
            required
            value={formData.bank}
            onChange={(e) => setFormData({...formData, bank: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select Bank</option>
            {BANKS.map((bank) => (
              <option key={bank} value={bank}>{bank}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Transaction Amount (₹) *</label>
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
          <label className="block text-sm font-medium text-gray-700 mb-2">Transaction Date *</label>
          <input
            type="date"
            required
            value={formData.date}
            onChange={(e) => setFormData({...formData, date: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Card Last 4 Digits</label>
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
          <label className="block text-sm font-medium text-gray-700 mb-2">Transaction ID (if available)</label>
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
        <label className="block text-sm font-medium text-gray-700 mb-2">Description *</label>
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
        onClick={onSubmit}
        className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center cursor-pointer"
      >
        Submit Report & Get Guidance
        <ArrowRight className="h-5 w-5 ml-2" />
      </button>
    </div>
  </div>
);

// Main Component
const BankingDisputePlatform: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [disputes, setDisputes] = useState<DisputeData[]>([]);
  const [selectedDispute, setSelectedDispute] = useState<DisputeData | null>(null);
  const [formData, setFormData] = useState<FormData>({
    type: '', amount: '', date: '', description: '',
    bank: '', cardLast4: '', transactionId: ''
  });
  const [guidance, setGuidance] = useState<GuidanceStep[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>('report');

  useEffect(() => {
    setDisputes(loadDisputes());
  }, []);

  const handleSubmit = () => {
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
      priority: calculatePriority(parseFloat(formData.amount)),
      bank: formData.bank,
      cardLast4: formData.cardLast4,
      createdAt: new Date().toISOString()
    };

    const updatedDisputes = [...disputes, newDispute];
    setDisputes(updatedDisputes);
    saveDisputes(updatedDisputes);
    
    setGuidance(generateGuidance(formData.type));
    setActiveTab('guidance');
    
    setFormData({
      type: '', amount: '', date: '', description: '',
      bank: '', cardLast4: '', transactionId: ''
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-lg border-b-4 border-blue-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="h-8 w-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">BankDispute Pro</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                <Clock className="inline h-4 w-4 mr-1" />
                24/7 Support Available
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="mb-8">
          <nav className="flex space-x-8">
           {
            TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg font-medium focus:outline-none ${
                  activeTab === tab.id 
                    ? 'bg-blue-600 text-white shadow-lg' 
                    : 'text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tab.label}
              </button>
            ))
           }
          </nav>
        </div>

        {/* Report Issue Tab */}
        {activeTab === 'report' && (
          <ReportForm 
            formData={formData}
            setFormData={setFormData}
            onSubmit={handleSubmit}
          />
        )}

        {/* Guidance Tab */}
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
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h3>
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
                                  {getTemplate(step.template, formData.type, formData)}
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
                          <div><span className="font-medium">Amount:</span> ₹{dispute.amount.toLocaleString()}</div>
                          <div><span className="font-medium">Bank:</span> {dispute.bank}</div>
                          <div><span className="font-medium">Date:</span> {new Date(dispute.date).toLocaleDateString()}</div>
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

      {/* Emergency Contacts Footer */}
      <footer className="bg-red-50 border-t-4 border-red-400 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-center space-x-8 text-sm">
            <div className="flex items-center text-red-800">
              <Phone className="h-4 w-4 mr-1" />
              <span className="font-medium">Emergency:</span> 1800-425-3800
            </div>
            <div className="flex items-center text-red-800">
              <Mail className="h-4 w-4 mr-1" />
              <span className="font-medium">Fraud Alert:</span> cybercrime@gov.in
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default BankingDisputePlatform;
