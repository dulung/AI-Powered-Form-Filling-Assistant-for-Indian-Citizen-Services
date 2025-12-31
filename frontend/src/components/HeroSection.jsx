import React from "react";
import { Link } from "react-router-dom";

export default function HeroSection() {
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-10 shadow-2xl">
      <h1 className="text-4xl md:text-5xl font-extrabold text-indigo-300 leading-tight">
        AI-powered form filling for Indian citizen services
      </h1>
      <p className="mt-4 text-gray-300 max-w-3xl">
        Upload Aadhaar, PAN or Voter ID — the assistant extracts fields using OCR, detects document type, and maps data into form templates for fast, accurate submissions.
      </p>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link to="/extract" className="bg-indigo-500 hover:bg-indigo-600 text-white px-5 py-2 rounded-lg">Try Demo</Link>
        <Link to="/about" className="text-indigo-300 px-5 py-2 rounded-lg border border-indigo-700">Learn more</Link>
      </div>
    </div>
  );
}