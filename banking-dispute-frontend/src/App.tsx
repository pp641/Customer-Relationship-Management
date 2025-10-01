import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import BankingDisputeChatbot from "./Components/BankingDisputeChatbot";
import DisputeAgentPortal from "./Components/BankingAgentPortal";
import Login from "./pages/Login";
import { AuthProvider } from "./context/authContext";
import ProtectedRoute from "./Components/ProtectedRoutes";
import EMICalculator from "./Components/EmiCalculator";
import FinancialDashboard from "./Components/MainDashboard";
import LoanEligibilityChecker from "./Components/LoanEligibilityChecker";
import FDRDCalculator from "./Components/FDRDCalculator";

// Dummy Protected Component for Testing
const DummyProtectedComponent: React.FC = () => {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center p-8 bg-white rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold text-green-600 mb-4">
          🎉 Protected Route Working!
        </h1>
        <p className="text-gray-600 mb-2">
          Hello! If you can see this, the protected route is loading correctly.
        </p>
        <p className="text-sm text-gray-500">
          You are successfully authenticated and viewing a protected component.
        </p>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/test-protected"
            element={
              <ProtectedRoute>
                <DummyProtectedComponent />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
                <FinancialDashboard />
            }
          />

          <Route
            path="/loan-checker"
            element={
                <LoanEligibilityChecker />
            }
          />

          <Route
            path="/fd-calculator"
            element={
                <FDRDCalculator />
            }
          />
          <Route path="/emi-calculator" element={
               <EMICalculator />
           } />
          <Route
            path="*"
            element={
              <div className="flex h-screen w-full">
                {/* Sidebar */}
                {/* <Sidebar /> */}

                {/* Main Content */}
                <main className="flex-1 p-6">
                  <Routes>
                    <Route
                      path="/portal"
                      element={
                        <ProtectedRoute>
                          <DisputeAgentPortal />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/chatbot"
                      element={
                        <ProtectedRoute>
                          <BankingDisputeChatbot />
                        </ProtectedRoute>
                      }
                    />
                    <Route path="/bank-data" element={<DisputeAgentPortal />} />
                    {/* Add dummy route here as well for testing */}
                    <Route
                      path="/dummy"
                      element={
                        <ProtectedRoute>
                          <DummyProtectedComponent />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="*"
                      element={
                        <ProtectedRoute>
                          <DisputeAgentPortal />
                        </ProtectedRoute>
                      }
                    />
                  </Routes>
                </main>
              </div>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
