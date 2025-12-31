import React from "react";

export default function AboutSection({ className = "" }) {
  return (
    <section className={`mt-10 ${className}`}>
      <div className="bg-gray-800 rounded-2xl p-8 shadow-lg">
        <h3 className="text-xl font-semibold text-indigo-300 mb-3">Project summary</h3>
        <p className="text-gray-300">
          This prototype automates extraction and mapping of identity data from document images to structured form templates. It demonstrates a practical pipeline that reduces manual data re-entry and speeds up citizen-facing workflows.
        </p>
      </div>
    </section>
  );
}