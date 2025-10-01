import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import BankingDisputeChatbot from "./Components/BankingDisputeChatbot";
import DisputeAgentPortal from "./Components/BankingAgentPortal";
import Login from "./pages/Login";
import { AuthProvider } from "./context/authContext";
import BankDataTable from './Components/BankingIFSC';
import ProtectedRoute from "./Components/ProtectedRoutes";


const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
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
                    <Route
                      path="/bank-data"
                      element={
                          <BankDataTable />
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

