import React from "react";

const requiredFields = ["name", "dob", "id_number", "address"]; // customize as needed

// Voice button component using Web Speech API
function VoiceInputButton({ onResult }) {
  function startListening() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech Recognition not supported in this browser.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.start();
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onResult(transcript);
    };
    recognition.onerror = (event) => {
      alert("Voice recognition error: " + event.error);
    };
  }

  return (
    <button
      type="button"
      onClick={startListening}
      title="Fill by speaking"
      style={{ marginLeft: "0.5rem", background: "#4338ca", color: "#fff", borderRadius: 6, padding: "0.4rem 0.7rem" }}
    >🎤</button>
  );
}

export default function ResultCard({ fields, onChange, onDownloadPdf, onReset }) {
  const entries = Object.entries(fields || {});

  return (
    <div className="bg-gray-800 rounded-2xl p-6 shadow-lg">
      <h3 className="text-xl font-semibold text-indigo-300 mb-4">
        Review & Edit Fields (required fields marked *)
      </h3>
      <form
        className="space-y-4"
        onSubmit={async (e) => {
          e.preventDefault();
          await onDownloadPdf();
        }}
      >
        {entries.map(([key, value]) => (
          <div key={key} className="flex flex-col">
            <label className="text-sm text-gray-300 mb-1">
              {key.charAt(0).toUpperCase() + key.slice(1)}
              {requiredFields.includes(key) && (
                <span className="ml-1 text-red-400">*</span>
              )}
            </label>
            <div style={{ display: "flex", alignItems: "center" }}>
              <input
                value={value || ""}
                onChange={(e) => onChange(key, e.target.value)}
                className={`bg-gray-900 border ${
                  requiredFields.includes(key) && (!value || value === "")
                    ? "border-red-400"
                    : "border-gray-700"
                } rounded-md px-3 py-2 text-white`}
                required={requiredFields.includes(key)}
              />
              <VoiceInputButton onResult={(text) => onChange(key, text)} />
            </div>
          </div>
        ))}
        <div className="flex gap-3 mt-6">
          <button
            type="submit"
            className="bg-green-600 hover:bg-green-700 font-bold text-white rounded-full px-4 py-2 shadow transition"
          >
            Download Filled PDF
          </button>
          <button
            type="button"
            className="bg-gray-700 hover:bg-gray-600 font-bold text-white rounded-full px-4 py-2 shadow"
            onClick={onReset}
          >
            Reset
          </button>
        </div>
      </form>
    </div>
  );
}