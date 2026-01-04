import React, { useState } from "react";
import UploadForm from "../UploadForm";
import ResultCard from "../components/ResultCard";

// CARD FIELD DEFINITIONS - Must match backend keys exactly
const aadhaarPanFields = [
  "Name",
  "Father Name",
  "Mother Name",
  "DOB",
  "Gender",
  "PAN",
  "Aadhaar",
  "Address",
];

const voterFields = [
  "Name",
  "EPIC Number",
  "DOB",
  "Gender",
  "Relation Name",
  "Relation Type",
  "Address",
];

const combinedFields = Array.from(
  new Set([...aadhaarPanFields, ...voterFields])
);

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

  // ✅ NEW: selected government form template
  const [template, setTemplate] = useState("birth_certificate");

  // ✅ TEMPLATE-AWARE DOWNLOAD FLOW
  async function handleDownloadPdf() {
    try {
      // 1️⃣ Map extracted fields to selected template
      const mapResp = await fetch("http://127.0.0.1:8000/map", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template,
          fields: result,
        }),
      });

      if (!mapResp.ok) throw new Error("Field mapping failed");
      const mapData = await mapResp.json();

      // 2️⃣ Generate template-based PDF
      const pdfResp = await fetch(
        "http://127.0.0.1:8000/generate-form-pdf",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            template,
            fields: mapData.mapped_fields,
          }),
        }
      );

      if (!pdfResp.ok) throw new Error("PDF generation failed");

      const blob = await pdfResp.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `${template}_filled.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("PDF download failed: " + (err.message || err));
    }
  }

  function resetAllFields() {
    if (!result) return;
    const blank = Object.fromEntries(Object.keys(result).map((k) => [k, ""]));
    setResult(blank);
  }

  const showStatus = status !== "idle" && status !== "error";

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Voice-only manual mode */}
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

      <div
        className={`transition-all duration-500 grid gap-8 ${
          showStatus ? "lg:grid-cols-3" : "lg:grid-cols-1"
        }`}
      >
        <div
          className={`transition-all duration-500 ${
            showStatus ? "lg:col-span-2" : "lg:col-span-3"
          }`}
        >
          <UploadForm
            onStart={() => {
              setStatus("uploading");
              setResult(null);
            }}
            onOCRStart={() => setStatus("ocr")}
            onResult={(payload) => {
              const cardKeys = fieldKeysForCard(payload.card_type || "");
              const values = Object.fromEntries(
                cardKeys.map((k) => [k, payload.fields?.[k] ?? ""])
              );
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
          <aside className="flex flex-col justify-start">
            <div className="bg-gray-900 rounded-3xl shadow-2xl border border-slate-700 px-8 py-10 w-full h-full flex flex-col gap-6">
              <h3 className="text-xl font-bold text-indigo-300">
                Select Government Form
              </h3>

              {/* ✅ TEMPLATE SELECTOR */}
              <select
                value={template}
                onChange={(e) => setTemplate(e.target.value)}
                className="bg-gray-800 text-white p-3 rounded-lg border border-gray-700"
              >
                <option value="birth_certificate">Birth Certificate</option>
<option value="bank_account">Bank Account</option>
<option value="pan_form">PAN Application</option>
<option value="generic_kyc">Generic KYC</option>
<option value="voter_id_application">Voter ID Application</option>
<option value="aadhaar_update">Aadhaar Update</option>
<option value="scholarship_application">Scholarship Application</option>
              </select>

              {cardType && (
                <div className="mt-4 text-indigo-200">
                  Detected Document:{" "}
                  <span className="font-bold uppercase">{cardType}</span>
                </div>
              )}
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