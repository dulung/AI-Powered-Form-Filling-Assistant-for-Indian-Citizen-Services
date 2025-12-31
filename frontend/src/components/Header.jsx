import React from "react";
import { Link, useLocation } from "react-router-dom";

export default function Header() {
  const loc = useLocation();
  return (
    <header className="bg-gray-900/60 backdrop-blur sticky top-0 z-40 border-b border-gray-800">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center text-black font-bold">AI</div>
          <div>
            <div className="text-sm font-semibold text-indigo-300">FormFill Assistant</div>
            <div className="text-xs text-gray-400">AI-powered document extractor</div>
          </div>
        </Link>

        <nav className="flex items-center space-x-2 bg-gray-800 px-3 py-2 rounded-full shadow-md">
  <Link
    to="/"
    className={`px-4 py-2 rounded-full transition ${
      loc.pathname === "/" ? "bg-indigo-600 text-white" : "text-indigo-200 hover:bg-indigo-700 hover:text-white"
    }`}
  >
    Home
  </Link>
  <Link
    to="/extract"
    className={`px-4 py-2 rounded-full transition ${
      loc.pathname === "/extract" ? "bg-indigo-600 text-white" : "text-indigo-200 hover:bg-indigo-700 hover:text-white"
    }`}
  >
    Extract
  </Link>
  <Link
    to="/about"
    className={`px-4 py-2 rounded-full transition ${
      loc.pathname === "/about" ? "bg-indigo-600 text-white" : "text-indigo-200 hover:bg-indigo-700 hover:text-white"
    }`}
  >
    About
  </Link>
</nav>
      </div>
    </header>
  );
}