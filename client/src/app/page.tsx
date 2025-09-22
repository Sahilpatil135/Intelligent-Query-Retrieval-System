"use client";

import React, { useState } from "react";
import axios from "axios";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [previousQueries, setPreviousQueries] = useState<{ q: string, a: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [references, setReferences] = useState<{ doc_name: string; page?: number }[]>([]);


  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus("Please select a file first");
      return;
    }
    setUploadStatus("Uploading...");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post("http://127.0.0.1:5000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadStatus("File uploaded & embedded successfully");
      console.log(res.data);
    } catch (err) {
      console.error(err);
      setUploadStatus("Error uploading file");
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post("http://127.0.0.1:5000/query", {
        query,
        top_k: 3,
      });
      setAnswer(res.data.answer);
      setReferences(res.data.references || []);
      setPreviousQueries([{ q: query, a: res.data.answer }, ...previousQueries]);
      console.log(res.data);
    } catch (err) {
      console.error(err);
      setAnswer("Error retrieving answer");
      setReferences([]);
    }
    setLoading(false);
  };

  const hasHistory = previousQueries.length > 0 || answer;

  return (
    <div
      className={`min-h-screen bg-gray-900 text-gray-100 flex flex-col items-center px-4 transition-all ${hasHistory ? "justify-start pt-8" : "justify-center"
        }`}
    >
      {/* Header */}
      <h1 className="text-4xl font-bold mt-6 mb-6 text-center bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
        Ask Anything
      </h1>

      {/* Upload Section */}
      <div className="w-full max-w-lg bg-gray-800 rounded-2xl shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-3">Upload Document</h2>
        <div className="flex items-center justify-between">
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={handleFileChange}
            className="text-gray-200"
          />
          <button
            onClick={handleUpload}
            className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg text-white"
          >
            Upload
          </button>
        </div>
        {uploadStatus && (
          <p className="text-sm text-gray-300 mt-2">{uploadStatus}</p>
        )}
      </div>

      {/* Chat Section */}
      <div className="w-full max-w-4xl bg-gray-800 rounded-2xl shadow p-6 flex flex-col space-y-4">
        {/* Previous Queries */}
        <div className="flex-1 overflow-y-auto max-h-96 space-y-4 pr-2">
          {previousQueries.length === 0 && (
            <p className="text-center text-gray-400">
              No previous queries yet. Start asking!
            </p>
          )}
          {previousQueries.map((item, idx) => (
            <div key={idx} className="space-y-2">
              <div className="bg-gray-700 rounded-lg p-3">
                <p className="font-semibold text-purple-300">You:</p>
                <p>{item.q}</p>
              </div>
              <div className="bg-gray-700 rounded-lg p-3">
                <p className="font-semibold text-green-300">AI:</p>
                <p>{item.a}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Input Box */}
        <div className="flex items-center space-x-4">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your question..."
            className="flex-1 bg-gray-700 rounded-lg p-3 text-gray-100 focus:outline-none resize-none"
            rows={2}
          />
          <button
            onClick={handleQuery}
            disabled={loading}
            className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg disabled:bg-gray-500 text-white"
          >
            {loading ? "..." : "Send"}
          </button>
        </div>
      </div>

      {/* Latest Answer */}
      {answer && (
        <div className="w-full max-w-2xl bg-gray-800 rounded-2xl shadow p-6 mt-6">
          <h2 className="text-lg font-semibold mb-3">Latest Answer</h2>
          {/* <div className="bg-gray-700 rounded-lg p-4">{answer}</div> */}

          {/* Render Markdown/HTML answer */}
          <div
            className="prose prose-invert max-w-none bg-gray-700 rounded-lg p-4"
            dangerouslySetInnerHTML={{ __html: answer }}
          />

          {/* Show references */}
          {references.length > 0 && (
            <div className="mt-4 text-sm text-gray-400">
              <p className="font-semibold">Sources:</p>
              <ul className="list-disc list-inside">
                {references.map((ref, idx) => (
                  <li key={idx}>
                    {ref.doc_name} {ref.page && `(page ${ref.page})`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
