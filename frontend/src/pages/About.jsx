import React from "react";
import { InformationCircleIcon, CheckBadgeIcon, WrenchScrewdriverIcon, ServerStackIcon } from "@heroicons/react/24/solid";

const content = [
  {
    icon: <InformationCircleIcon className="w-8 h-8 text-indigo-400 mb-2" />,
    title: "Problem",
    color: "indigo-300",
    body: (
      <>
        Citizens must repeatedly enter the same identity data into multiple government and private forms. Manual data entry is time-consuming and error-prone.<br /><br />
        This project automates the extraction of fields from identity documents and maps them onto form templates to reduce effort and errors.
      </>
    ),
  },
  {
    icon: <CheckBadgeIcon className="w-8 h-8 text-green-400 mb-2" />,
    title: "Solution",
    color: "green-300",
    body: (
      <>
        Uses OCR to extract text from images (Aadhaar, PAN, Voter ID), classifies document type, runs specialized extractors, and maps fields into templates.<br /><br />
        Fields can be reviewed, edited, exported for submission.
      </>
    ),
  },
  {
    icon: <WrenchScrewdriverIcon className="w-8 h-8 text-yellow-300 mb-2" />,
    title: "Pipeline",
    color: "yellow-300",
    body: (
      <ol className="list-decimal list-inside space-y-1 ml-2">
        <li><span className="font-bold text-indigo-200">Upload</span> or capture a document image</li>
        <li><span className="font-bold text-indigo-200">Preprocess</span> image</li>
        <li><span className="font-bold text-indigo-200">OCR</span> with Tesseract</li>
        <li><span className="font-bold text-indigo-200">Detect type</span> (PAN/Aadhaar/Voter ID)</li>
        <li><span className="font-bold text-indigo-200">Extract</span> fields via specialized extractor</li>
        <li><span className="font-bold text-indigo-200">Map</span> fields to form template</li>
      </ol>
    ),
  },
  {
    icon: <ServerStackIcon className="w-8 h-8 text-blue-400 mb-2" />,
    title: "Technical Notes",
    color: "blue-300",
    body: (
      <>
        <span className="font-bold">Backend:</span> FastAPI, OpenCV, pytesseract<br />
        <span className="font-bold">Frontend:</span> React, Vite, TailwindCSS<br />
        <span className="font-bold">Mapping:</span> JSON-based templates, fuzzy matching
      </>
    ),
  },
];

export default function About() {
  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      {/* Title Section */}
      <div className="mb-12 bg-gradient-to-br from-indigo-900/40 via-gray-900/70 to-gray-800/80 rounded-2xl p-10 shadow-2xl border border-indigo-700 text-center">
        <h2 className="text-4xl font-extrabold text-indigo-200 mb-2 drop-shadow">
          AI-Powered Form Filling Assistant
        </h2>
        <p className="text-lg text-gray-300 max-w-2xl mx-auto">
          Innovating citizen workflows by automating extraction and mapping of identity data from government documents.
        </p>
      </div>

      {/* 4-Box Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        {content.map((item, idx) => (
          <div
            key={idx}
            className={`bg-gradient-to-b from-gray-800 to-gray-900 rounded-2xl p-7 shadow-xl border border-gray-700 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl cursor-pointer group`}
            style={{ minHeight: '290px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start' }}
          >
            <div>{item.icon}</div>
            <h3 className={`text-xl font-bold text-${item.color} mb-2 group-hover:text-white`}>
              {item.title}
            </h3>
            <div className="text-gray-300 text-[15px]">{item.body}</div>
          </div>
        ))}
      </div>
    </div>
  );
}