import { useState } from 'react';
import { Calculator, Settings, User, LogOut, PiggyBank, TrendingUp, CreditCard, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

type TabType = 'calculators' | 'settings' | 'profile';


export default function FinancialDashboard() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabType>('calculators');
  const [userName] = useState('John Doe');

  const calculators = [
    {
      id: 'emi' as const,
      name: 'EMI Calculator',
      description: 'Calculate your loan EMI and payment schedule',
      icon: CreditCard,
      color: 'blue',
      route: '/emi-calculator',
    },
    {
      id: 'eligibility' as const,
      name: 'Loan Eligibility Checker',
      description: 'Check your loan eligibility and get recommendations',
      icon: TrendingUp,
      color: 'purple',
      route: '/loan-checker',
    },
    {
      id: 'fdrd' as const,
      name: 'FD/RD Calculator',
      description: 'Calculate returns on Fixed and Recurring Deposits',
      icon: PiggyBank,
      color: 'green',
      route: '/fd-calculator',
    },
  ];

  const tabs = [
    { id: 'calculators' as const, name: 'Calculators', icon: Calculator },
    { id: 'settings' as const, name: 'Settings', icon: Settings },
    { id: 'profile' as const, name: 'Profile', icon: User },
  ];

  const handleLogout = () => {
    localStorage.clear()
      navigate('/login');
    }
  

  const handleCalculatorClick = (route: string) => {
            navigate(route)
    }
  

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Vertical Sidebar */}
      <div className="w-64 bg-gradient-to-b from-indigo-600 to-indigo-800 text-white flex flex-col shadow-xl">
        <div className="p-6 border-b border-indigo-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
              <Calculator className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h1 className="text-lg font-bold">FinCalc Pro</h1>
              <p className="text-xs text-indigo-200">Financial Tools</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {tabs.map((tab) => (
              <li key={tab.id}>
                <button
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                    activeTab === tab.id
                      ? 'bg-white text-indigo-600 shadow-lg'
                      : 'text-indigo-100 hover:bg-indigo-700'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  <span className="font-medium">{tab.name}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <div className="p-4 border-t border-indigo-500">
          <div className="flex items-center gap-3 px-4 py-3 bg-indigo-700 rounded-lg mb-3">
            <div className="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center">
              <User className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">{userName}</p>
              <p className="text-xs text-indigo-300">Premium User</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-2 text-indigo-100 hover:bg-indigo-700 rounded-lg transition"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-8">
          {/* Header */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-800 mb-2">
              {activeTab === 'calculators' && 'Financial Calculators'}
              {activeTab === 'settings' && 'Settings'}
              {activeTab === 'profile' && 'Profile'}
            </h2>
            <p className="text-gray-600">
              {activeTab === 'calculators' && 'Choose a calculator to get started with your financial planning'}
              {activeTab === 'settings' && 'Manage your preferences and application settings'}
              {activeTab === 'profile' && 'View and edit your profile information'}
            </p>
          </div>

          {/* Content based on active tab */}
          {activeTab === 'calculators' && (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {calculators.map((calc) => (
                <button
                  key={calc.id}
                  onClick={() => handleCalculatorClick(calc.route)}
                  className="bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border-2 border-transparent hover:border-indigo-200 group text-left"
                >
                  <div className={`w-12 h-12 ${calc.color === 'blue' ? 'bg-blue-100' : calc.color === 'purple' ? 'bg-purple-100' : 'bg-green-100'} rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition`}>
                    <calc.icon className={`w-6 h-6 ${calc.color === 'blue' ? 'text-blue-600' : calc.color === 'purple' ? 'text-purple-600' : 'text-green-600'}`} />
                  </div>
                  <h3 className="text-xl font-bold text-gray-800 mb-2">{calc.name}</h3>
                  <p className="text-gray-600 text-sm mb-4">{calc.description}</p>
                  <div className="flex items-center text-indigo-600 font-medium text-sm">
                    <span>Open Calculator</span>
                    <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition" />
                  </div>
                </button>
              ))}
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="bg-white rounded-xl p-8 shadow-md max-w-2xl">
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-gray-800 mb-4">General Settings</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-800">Currency Format</p>
                        <p className="text-sm text-gray-600">INR (₹)</p>
                      </div>
                      <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">
                        Change
                      </button>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-800">Default Calculator</p>
                        <p className="text-sm text-gray-600">EMI Calculator</p>
                      </div>
                      <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">
                        Change
                      </button>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-800">Theme</p>
                        <p className="text-sm text-gray-600">Light Mode</p>
                      </div>
                      <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">
                        Toggle
                      </button>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-gray-800 mb-4">Notifications</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-800">Email Notifications</p>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" defaultChecked />
                        <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                      </label>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-800">SMS Alerts</p>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" />
                        <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'profile' && (
            <div className="bg-white rounded-xl p-8 shadow-md max-w-2xl">
              <div className="flex items-center gap-6 mb-8">
                <div className="w-24 h-24 bg-indigo-100 rounded-full flex items-center justify-center">
                  <User className="w-12 h-12 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-800">{userName}</h3>
                  <p className="text-gray-600">john.doe@example.com</p>
                  <button className="mt-2 px-4 py-1.5 bg-indigo-100 text-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-200">
                    Edit Profile
                  </button>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <h4 className="text-lg font-bold text-gray-800 mb-4">Account Information</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-gray-600">Member Since</span>
                      <span className="font-medium text-gray-800">January 2024</span>
                    </div>
                    <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-gray-600">Account Type</span>
                      <span className="font-medium text-gray-800">Premium</span>
                    </div>
                    <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-gray-600">Calculations Done</span>
                      <span className="font-medium text-gray-800">247</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-bold text-gray-800 mb-4">Security</h4>
                  <div className="space-y-3">
                    <button className="w-full p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition text-left">
                      <p className="font-medium text-gray-800">Change Password</p>
                      <p className="text-sm text-gray-600">Last changed 30 days ago</p>
                    </button>
                    <button className="w-full p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition text-left">
                      <p className="font-medium text-gray-800">Two-Factor Authentication</p>
                      <p className="text-sm text-gray-600">Not enabled</p>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}