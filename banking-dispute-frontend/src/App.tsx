import React from "react";
import { BrowserRouter as Router, Routes, Route, NavLink, useNavigate } from "react-router-dom";
import BankingDisputeChatbot from "./Components/BankingDisputeChatbot";
import DisputeAgentPortal from "./Components/BankingAgentPortal";
import Login from "./pages/Login";
import { AuthProvider, useAuth } from "./context/authContext";
import BankDataTable from './Components/BankingIFSC';
import ProtectedRoute from "./Components/ProtectedRoutes";

const Sidebar: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="w-48 bg-gray-100 p-4 flex flex-col space-y-4 border-r">
      <NavLink
        to="/portal"
        className={({ isActive }) =>
          `p-2 rounded-lg ${isActive ? "bg-blue-500 text-white" : "hover:bg-blue-200"}`
        }
      >
        Portal
      </NavLink>
      <NavLink
        to="/chatbot"
        className={({ isActive }) =>
          `p-2 rounded-lg ${isActive ? "bg-blue-500 text-white" : "hover:bg-blue-200"}`
        }
      >
        Chatbot
      </NavLink>
      <NavLink
        to="/bank-data"
        className={({ isActive }) =>
          `p-2 rounded-lg ${isActive ? "bg-blue-500 text-white" : "hover:bg-blue-200"}`
        }
      >
        Bank Data
      </NavLink>

      {/* Logout Button */}
      <button
        onClick={handleLogout}
        className="p-2 rounded-lg bg-red-500 text-white hover:bg-red-600 mt-auto"
      >
        Logout
      </button>
    </nav>
  );
};

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
