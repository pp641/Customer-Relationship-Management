import React, { useState, useRef, type ChangeEvent,  type JSX } from "react";

// Type definitions
type ContextType = 'setup' | 'problem' | 'explore';
type IssueType = 'kyc' | 'missed_txn' | 'name_mismatch';
type IdType = 'AADHAAR' | 'PAN' | 'PASSPORT';

interface FormData {
  fullName: string;
  dob: string;
  idType: IdType;
  idNumber: string;
  accountNumber: string;
  txnDate: string;
  txnAmount: string;
  txnId: string;
  wrongName: string;
  correctName: string;
  description: string;
}

interface ApiResponse {
  ticketId?: string;
}

// Banking Chatbot - Improved guided onboarding flow
// Flow: Welcome → Context → Issue → Form → Review → Submit
const ChatbotFlow: React.FC = () => {
  const [step, setStep] = useState<number>(0);
  const [context, setContext] = useState<ContextType | null>(null);
  const [selected, setSelected] = useState<IssueType | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [form, setForm] = useState<FormData>({
    fullName: "",
    dob: "",
    idType: "AADHAAR",
    idNumber: "",
    accountNumber: "",
    txnDate: "",
    txnAmount: "",
    txnId: "",
    wrongName: "",
    correctName: "",
    description: "",
  });
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleContextSelect = (contextValue: ContextType): void => {
    setContext(contextValue);
    if (contextValue === "setup") {
      setSelected("kyc");
      setStep(2); // go directly to form
    } else if (contextValue === "problem") {
      setStep(1); // go to problem options
    } else if (contextValue === "explore") {
      setStep(99); // explore features placeholder
    }
  };

  const handleSelectIssue = (key: IssueType): void => {
    setSelected(key);
    setStep(2);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setForm((prevState) => ({ ...prevState, [name]: value }));
  };

  const handleFile = (event: ChangeEvent<HTMLInputElement>): void => {
    const selectedFile = event.target.files?.[0] ?? null;
    setFile(selectedFile);
  };

  const goBack = (): void => {
    if (step === 1) {
      setContext(null);
      setStep(0);
    } else if (step === 2) {
      if (context === "setup") {
        setContext(null);
        setSelected(null);
        setStep(0);
      } else {
        setSelected(null);
        setStep(1);
      }
    } else if (step > 2 && step < 99) {
      setStep((prevStep) => prevStep - 1);
    } else if (step === 99) {
      setContext(null);
      setStep(0);
    }
  };

  const handleSubmit = async (): Promise<void> => {
    if (!selected) return;

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("type", selected);
      formData.append("payload", JSON.stringify(form));
      if (file) {
        formData.append("attachment", file);
      }

      const response = await fetch("/api/support/submit", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Network error");
      }

      const data: ApiResponse = await response.json();
      setTicketId(data.ticketId ?? `TICKET-${Math.floor(Math.random() * 90000) + 10000}`);
      setStep(4);
    } catch (error) {
      console.error("Submission error:", error);
      alert("Failed to submit. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const renderForm = (): JSX.Element | null => {
    switch (selected) {
      case "kyc":
        return (
          <div className="space-y-3">
            <label className="block">
              <div className="text-sm font-medium">Full name</div>
              <input 
                name="fullName" 
                value={form.fullName} 
                onChange={handleChange} 
                className="mt-1 block w-full rounded-md border p-2"
                type="text"
                required
              />
            </label>
            <label className="block">
              <div className="text-sm font-medium">Date of birth</div>
              <input 
                type="date" 
                name="dob" 
                value={form.dob} 
                onChange={handleChange} 
                className="mt-1 block w-full rounded-md border p-2"
                required
              />
            </label>
            <label className="block">
              <div className="text-sm font-medium">ID number</div>
              <input 
                name="idNumber" 
                value={form.idNumber} 
                onChange={handleChange} 
                className="mt-1 block w-full rounded-md border p-2"
                type="text"
                required
              />
            </label>
            <input 
              ref={fileRef} 
              onChange={handleFile} 
              type="file" 
              accept="image/*,.pdf" 
              className="mt-2"
            />
            <div className="flex justify-between pt-4">
              <button 
                onClick={goBack} 
                className="px-4 py-2 rounded bg-gray-100"
                type="button"
              >
                Back
              </button>
              <button 
                onClick={() => setStep(3)} 
                className="px-4 py-2 rounded bg-indigo-600 text-white"
                type="button"
              >
                Next
              </button>
            </div>
          </div>
        );
      case "missed_txn":
        return (
          <div className="space-y-3">
            <label className="block">
              <div className="text-sm font-medium">Account number</div>
              <input 
                name="accountNumber" 
                value={form.accountNumber} 
                onChange={handleChange} 
                className="mt-1 block w-full rounded-md border p-2"
                type="text"
                required
              />
            </label>
            <label className="block">
              <div className="text-sm font-medium">Transaction date</div>
              <input 
                type="date" 
                name="txnDate" 
                value={form.txnDate} 
                onChange={handleChange} 
                className="mt-1 block w-full rounded-md border p-2"
                required
              />
            </label>
            <label className="block">
              <div className="text-sm font-medium">Amount</div>
              <input 
                name="txnAmount" 
                value={form.txnAmount} 
                onChange={handleChange} 
                className="mt-1 block w-full rounded-md border p-2"
                type="number"
                step="0.01"
                required
              />
            </label>
            <input 
              ref={fileRef} 
              onChange={handleFile} 
              type="file" 
              accept="image/*,.pdf" 
              className="mt-2"
            />
            <div className="flex justify-between pt-4">
              <button 
                onClick={goBack} 
                className="px-4 py-2 rounded bg-gray-100"
                type="button"
              >
                Back
              </button>
              <button 
                onClick={() => setStep(3)} 
                className="px-4 py-2 rounded bg-indigo-600 text-white"
                type="button"
              >
                Next
              </button>
            </div>
          </div>
        );
      case "name_mismatch":
        return (
          <div className="space-y-3">
            <label className="block">
              <div className="text-sm font-medium">Account number</div>
              <input 
                name="accountNumber" 
                value={form.accountNumber} 
                onChange={handleChange} 
                className="mt-1 block w-full rounded-md border p-2"
                type="text"
                required
              />
            </label>
            <label className="block">
              <div className="text-sm font-medium">Correct name</div>
              <input 
                name="correctName" 
                value={form.correctName} 
                onChange={handleChange} 
                className="mt-1 block w-full rounded-md border p-2"
                type="text"
                required
              />
            </label>
            <input 
              ref={fileRef} 
              onChange={handleFile} 
              type="file" 
              accept="image/*,.pdf" 
              className="mt-2"
            />
            <div className="flex justify-between pt-4">
              <button 
                onClick={goBack} 
                className="px-4 py-2 rounded bg-gray-100"
                type="button"
              >
                Back
              </button>
              <button 
                onClick={() => setStep(3)} 
                className="px-4 py-2 rounded bg-indigo-600 text-white"
                type="button"
              >
                Next
              </button>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  const renderReview = (): JSX.Element => {
    return (
      <div className="space-y-4">
        <div className="text-sm text-gray-600">Review your information</div>
        <pre className="bg-gray-50 p-3 rounded text-xs max-h-40 overflow-auto">
          {JSON.stringify(form, null, 2)}
        </pre>
        <div>Attachment: {file ? file.name : "No file attached"}</div>
        <div className="flex justify-between pt-4">
          <button 
            onClick={goBack} 
            className="px-4 py-2 rounded bg-gray-100"
            type="button"
          >
            Back
          </button>
          <button 
            onClick={handleSubmit} 
            disabled={submitting} 
            className="px-4 py-2 rounded bg-green-600 text-white disabled:opacity-50"
            type="button"
          >
            {submitting ? "Submitting..." : "Submit"}
          </button>
        </div>
      </div>
    );
  };

  const resetForm = (): void => {
    setStep(0);
    setContext(null);
    setSelected(null);
    setTicketId(null);
    setFile(null);
    setForm({
      fullName: "",
      dob: "",
      idType: "AADHAAR",
      idNumber: "",
      accountNumber: "",
      txnDate: "",
      txnAmount: "",
      txnId: "",
      wrongName: "",
      correctName: "",
      description: "",
    });
  };

  return (
    <div className="max-w-md mx-auto mt-6 p-4 rounded-lg shadow-lg bg-white">
      <h3 className="text-lg font-semibold">Support Chatbot</h3>
      <div className="mt-3">
        {step === 0 && (
          <div className="space-y-3">
            <div className="text-sm text-gray-600">Hi 👋 Welcome aboard! I can help you get started.</div>
            <div className="grid gap-2">
              <button 
                onClick={() => handleContextSelect("setup")} 
                className="px-4 py-3 rounded border hover:bg-gray-50"
                type="button"
              >
                🔑 Set up my account
              </button>
              <button 
                onClick={() => handleContextSelect("problem")} 
                className="px-4 py-3 rounded border hover:bg-gray-50"
                type="button"
              >
                ⚡ Problem with my account
              </button>
              <button 
                onClick={() => handleContextSelect("explore")} 
                className="px-4 py-3 rounded border hover:bg-gray-50"
                type="button"
              >
                📖 Explore features
              </button>
            </div>
          </div>
        )}
        {step === 1 && (
          <div className="space-y-3">
            <div className="text-sm text-gray-600">What kind of problem are you facing?</div>
            <div className="grid gap-2">
              <button 
                onClick={() => handleSelectIssue("missed_txn")} 
                className="px-4 py-3 rounded border hover:bg-gray-50"
                type="button"
              >
                💸 A transaction is missing
              </button>
              <button 
                onClick={() => handleSelectIssue("name_mismatch")} 
                className="px-4 py-3 rounded border hover:bg-gray-50"
                type="button"
              >
                📝 My name/details don't match
              </button>
              <button 
                onClick={goBack} 
                className="px-4 py-3 rounded border hover:bg-gray-50"
                type="button"
              >
                ⬅️ Back
              </button>
            </div>
          </div>
        )}
        {step === 2 && renderForm()}
        {step === 3 && renderReview()}
        {step === 4 && (
          <div className="space-y-3 text-center py-6">
            <div className="text-green-600 font-semibold">Submitted successfully!</div>
            <div className="text-sm">Your ticket ID: <span className="font-mono">{ticketId}</span></div>
            <button 
              onClick={resetForm} 
              className="mt-4 px-4 py-2 rounded bg-indigo-600 text-white"
              type="button"
            >
              Start new request
            </button>
          </div>
        )}
        {step === 99 && (
          <div className="space-y-3">
            <div className="text-sm text-gray-600">Here are some things you can explore:</div>
            <ul className="list-disc list-inside text-sm text-gray-700">
              <li>💳 How to apply for a debit/credit card</li>
              <li>📱 Mobile app features</li>
              <li>🔔 Setting up transaction alerts</li>
            </ul>
            <button 
              onClick={goBack} 
              className="px-4 py-2 rounded bg-gray-100"
              type="button"
            >
              Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatbotFlow;
