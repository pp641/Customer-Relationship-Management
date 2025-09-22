import { Mail, Phone } from "lucide-react";
import React from "react";

const FooterComponent : React.FC = () => {
    return(
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
    )
}

export default FooterComponent