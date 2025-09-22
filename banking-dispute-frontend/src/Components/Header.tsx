import { Clock, Shield } from "lucide-react";
import React from "react";

const Header : React.FC = () => {
    return(
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
    )
}

export default Header