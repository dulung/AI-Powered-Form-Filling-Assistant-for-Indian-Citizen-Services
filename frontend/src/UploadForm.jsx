import React, { useState } from "react";
import Loader from "./components/Loader";

export default function UploadForm({ onStart, onOCRStart, onResult, onError }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    setFile(selected);
    if (selected) setPreview(URL.createObjectURL(selected));
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
  };

  const handleUpload = async (e) => {
    e?.preventDefault();
    if (!file) {
      onError && onError("Please select a file first!");
      return;
    }
    onStart && onStart();
    setLoading(true);
    onOCRStart && onOCRStart();

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/extract", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      onResult && onResult(data);
    } catch (err) {
      onError && onError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-2xl shadow-2xl p-8">
      <form onSubmit={handleUpload} className="flex flex-col items-center space-y-4">
        <label className="w-full border-2 border-dashed border-gray-500 rounded-xl p-6 text-center cursor-pointer hover:border-indigo-400 transition-all">
          {preview ? (
            <img src={preview} alt="Preview" className="w-48 mx-auto rounded-lg mb-3 shadow-md" />
          ) : (
            <span className="text-gray-400">Drag and drop a file or click to browse</span>
          )}
          <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
        </label>

        {loading ? (
          <Loader text="Extracting fields, please wait..." />
        ) : (
        <div className="flex gap-3">
          <button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-5 py-2 rounded-full shadow transition disabled:opacity-60" disabled={loading || !file}>
            Upload & Extract
          </button>
          <button type="button" className="bg-gray-700 hover:bg-gray-600 text-white font-bold px-4 py-2 rounded-full shadow" onClick={handleReset} disabled={loading}>
            Reset
          </button>
        </div>
        )}
      </form>
    </div>
  );
}