import React, { useState } from "react";
import UploadForm from "./UploadForm";
import ResultCard from "./components/ResultCard";
import Header from "./components/Header";

function Modal({ message, type, onClose }) {
  return (
    <div className="fixed z-50 inset-0 bg-black/30 flex items-center justify-center">
      <div className={`bg-gray-900 border rounded-xl px-8 py-5 flex flex-col items-center min-w-[320px] shadow-2xl border-${type === "success" ? "green-500" : "red-500"}`}>
        <div className={`text-xl font-bold mb-2 ${type === "success" ? "text-green-400" : "text-red-400"}`}>{type === "success" ? "Success" : "Error"}</div>
        <div className="text-gray-200 mb-4">{message}</div>
        <button className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-5 py-1.5 font-semibold mt-2" onClick={onClose}>OK</button>
      </div>
    </div>
  );
}

export default function App() {
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [modal, setModal] = useState(null);

  async function handleDownloadPdf(fields) {
  console.log("Download PDF called with fields:", fields);
  try {
    const resp = await fetch("http://127.0.0.1:8000/generate-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        template: "default",
        fields,
      }),
    });
    console.log("PDF download status:", resp.status);
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
    setModal({ message: "PDF downloaded successfully!", type: "success" });
  } catch (err) {
    console.error("Download PDF error:", err);
    setModal({ message: "PDF download failed: " + (err.message || err), type: "error" });
  }
}

function resetAllFields() {
  console.log("Reset called for fields:", result);
  if (!result) return;
  const cleared = Object.fromEntries(Object.keys(result).map((k) => [k, ""]));
  setResult(cleared);
}

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
      <Header />
      {modal && (
        <Modal
          message={modal.message}
          type={modal.type}
          onClose={() => setModal(null)}
        />
      )}
      <main className="max-w-5xl mx-auto px-6 py-10 space-y-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <UploadForm
              onStart={() => {
                setStatus("uploading");
                setResult(null);
              }}
              onOCRStart={() => setStatus("ocr")}
              onResult={(payload) => {
                setResult(payload.fields || {});
                setStatus(payload.fields ? "done" : "error");
                setModal({ message: "Extraction complete!", type: "success" });
              }}
              onError={(err) => {
                setStatus("error");
                setModal({ message: typeof err === "string" ? err : "Upload or extraction failed.", type: "error" });
                console.error("Upload error:", err);
              }}
            />
          </div>
        </div>
        {result && (
          <div className="mt-10">
            <ResultCard
              fields={result}
              onChange={(k, v) => setResult({ ...result, [k]: v })}
              onDownloadPdf={() => handleDownloadPdf(result)}
              onReset={resetAllFields}
            />
          </div>
        )}
      </main>
    </div>
  );
}