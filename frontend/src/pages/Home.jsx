import React from "react";
import HeroSection from "../components/HeroSection";
import AboutSection from "../components/AboutSection";
import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <HeroSection />

      <div className="mt-12 grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* LEFT COLUMN */}
        <div className="lg:col-span-2 space-y-8">

          {/* 🎬 TUTORIAL VIDEO CARD */}
          <div className="bg-gray-800 rounded-2xl p-6 shadow-lg">
            <h3 className="text-xl font-semibold text-indigo-300 mb-4">
              How to use this app? Here's a video tutorial ⬇️
            </h3>

            <div className="w-full aspect-video rounded-xl overflow-hidden shadow-lg">
              <iframe
                className="w-full h-full"
                src="https://youtube.com/embed/UL7LyLC9S0I"
                title="Tutorial Video"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              ></iframe>
            </div>
          </div>

        </div>

        {/* RIGHT SIDEBAR */}
        <aside className="space-y-6">
          <div className="bg-gray-800 rounded-2xl p-6 shadow-lg">
            <h4 className="text-lg font-semibold text-indigo-300 mb-2">
              Why this project ?
            </h4>
            <p className="text-gray-300 text-sm">
              This project automates document data extraction and maps fields to
              government/service forms to speed up citizen services.
            </p>
          </div>

          <div className="bg-gray-800 rounded-2xl p-6 shadow-lg">
            <h4 className="text-lg font-semibold text-indigo-300 mb-2">
              Quick links
            </h4>

            <ul className="text-sm text-gray-300 space-y-2">
              <li>
                <Link to="/about" className="text-indigo-300 hover:underline">
                  Project details
                </Link>
              </li>

              <li>
                <Link to="/extract" className="text-indigo-300 hover:underline">
                  Use extractor
                </Link>
              </li>
            </ul>
          </div>
        </aside>
      </div>

      <AboutSection className="mt-12" />
    </div>
  );
}
