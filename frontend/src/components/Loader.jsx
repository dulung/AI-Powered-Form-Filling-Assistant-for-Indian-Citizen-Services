import React from "react";

export default function Loader({ text = "Processing..." }) {
  return (
    <div className="flex flex-col items-center justify-center space-y-2 py-4">
      <svg className="animate-spin h-8 w-8 text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokekeWidth="4"/>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
      <span className="text-indigo-200 font-medium">{text}</span>
    </div>
  );
}