import React from "react";
// import BankingDisputePlatform from "./BankingDisputeForm";
// import Tester from './Components/Tester'
// import BankingDisputeChatbot from "./Components/TestComponent";
import BankingDisputeChatbot from "./Components/BankingDisputeChatbot";
import DisputeAgentPortal from "./Components/BankingAgentPortal";

const App  : React.FC = () => {
    return(
      <>
      <BankingDisputeChatbot/>
      <DisputeAgentPortal/>
      </>
    )
}

export default App;