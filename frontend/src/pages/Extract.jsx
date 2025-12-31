import React, { useState } from "react";
import UploadForm from "../UploadForm";
import ResultCard from "../components/ResultCard";

// CARD FIELD DEFINITIONS - These must match backend keys exactly!
const aadhaarPanFields = [
  "Name", "Father Name", "Mother Name", "DOB", "Gender", "PAN", "Aadhaar", "Address"
];
const voterFields = [
  "Name", "EPIC Number", "DOB", "Gender", "Relation Name", "Relation Type", "Address"
];
const combinedFields = Array.from(new Set([...aadhaarPanFields, ...voterFields]));

function emptyFields(keys) {
  return Object.fromEntries(keys.map((k) => [k, ""]));
}

function fieldKeysForCard(typeString) {
  if (!typeString) return [];
  const type = typeString.toLowerCase();
  if (type.includes("aadhaar") || type.includes("pan")) return aadhaarPanFields;
  if (type.includes("voter")) return voterFields;
  return combinedFields;
}

export default function Extract() {
  const [result, setResult] = useState(null);
  const [cardType, setCardType] = useState(null);
  const [status, setStatus] = useState("idle");

  async function handleDownloadPdf() {
    try {
      const resp = await fetch("http://127.0.0.1:8000/generate-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template: "default",
          fields: result,
        }),
      });
      if (!resp.ok) throw new Error("Failed to generate PDF");
      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "filled_form.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      alert("PDF downloaded successfully!");
    } catch (err) {
      alert("PDF download failed: " + (err.message || err));
    }
  }

  function resetAllFields() {
    if (!result) return;
    const blank = Object.fromEntries(Object.keys(result).map((k) => [k, ""]));
    setResult(blank);
  }

  const showStatus = (status !== "idle" && status !== "error");

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <button
        className="bg-indigo-600 text-white rounded px-4 py-2 font-bold mb-4"
        onClick={() => {
          setResult(emptyFields(combinedFields));
          setStatus("done");
          setCardType("VOICE");
        }}
      >
        Fill Manually via Voice
      </button>
      <div className={`transition-all duration-500 grid gap-8 ${showStatus ? "lg:grid-cols-3" : "lg:grid-cols-1"}`}>
        <div className={`transition-all duration-500 ${showStatus ? "lg:col-span-2" : "lg:col-span-3"}`}>
          <UploadForm
            onStart={() => {
              setStatus("uploading");
              setResult(null);
            }}
            onOCRStart={() => setStatus("ocr")}
            onResult={(payload) => {
              console.log('Extracted fields:', payload.fields);
              console.log('Card type:', payload.card_type);
              const cardKeys = fieldKeysForCard(payload.card_type || "");
              // Use values if they exist; otherwise, blank
              const values = Object.fromEntries(cardKeys.map(
                k => [k, payload.fields?.[k] ?? ""]
              ));
              setResult(values);
              setCardType(payload.card_type || null);
              setStatus(cardKeys.length ? "done" : "error");
            }}
            onError={(err) => {
              setStatus("error");
              console.error("Upload error:", err);
            }}
          />
        </div>
        {showStatus && (
          <aside className="transition-all duration-500 flex flex-col justify-start">
            <div className="bg-gradient-to-br from-gray-900/95 via-gray-800/90 to-gray-900/80 rounded-3xl shadow-2xl border border-slate-700/60 px-8 py-10 w-full h-full flex flex-col items-center gap-6">
              <div className="flex items-center gap-3 mb-2">
                {status === "done" && (
                  <svg className="w-8 h-8 text-green-400 drop-shadow-lg" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" className="stroke-current opacity-20" />
                    <path strokeLinecap="round" strokeLinejoin="round" className="stroke-current" d="M6 13l4 4 6-8" />
                  </svg>
                )}
                {status === "ocr" && (
                  <svg className="w-8 h-8 text-indigo-300 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                )}
                <h3 className="text-2xl font-bold tracking-tight text-indigo-200 drop-shadow">
                  {status === "uploading" && "Uploading..."}
                  {status === "ocr" && "Recognizing Text..."}
                  {status === "done" && "Ready!"}
                  {status === "idle" && "Status"}
                  {status === "error" && "Error"}
                </h3>
              </div>
              <div className="mt-2 w-full flex flex-col gap-2">
                {status === "uploading" && (
                  <span className="text-base text-indigo-200/80">Your file is being uploaded. Please wait.</span>
                )}
                {status === "ocr" && (
                  <span className="text-base text-indigo-200/80">Extracting all data from your document.</span>
                )}
                {status === "done" && (
                  <div className="flex items-center gap-2 text-green-300 font-semibold text-lg">
                    Extraction complete <span className="animate-bounce">✅</span>
                  </div>
                )}
                {status === "error" && (
                  <span className="text-base text-red-400">There was a problem. Please try again.</span>
                )}
                {status === "idle" && (
                  <span className="text-base text-slate-400">Waiting for upload…</span>
                )}
              </div>
              {cardType && (
                <div className="mt-5 self-center bg-indigo-700/20 px-4 py-2 rounded-full shadow text-indigo-200 text-base font-semibold tracking-wide">
                  <span className="text-indigo-100 font-light">Detected: </span>
                  <span className="uppercase tracking-wider font-extrabold">{cardType}</span>
                </div>
              )}
              <div className="mt-8 opacity-60 text-xs tracking-wide text-slate-400">
                Powered by <span className="text-indigo-400 font-semibold">FormFill AI</span>
              </div>
            </div>
          </aside>
        )}
      </div>
      {result && (
        <div className="mt-10">
          <ResultCard
            fields={result}
            onChange={(k, v) => setResult({ ...result, [k]: v })}
            onDownloadPdf={handleDownloadPdf}
            onReset={resetAllFields}
          />
        </div>
      )}
    </div>
  );
}