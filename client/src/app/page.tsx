"use client";

import React, { useState } from "react";
import axios from "axios";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [previousQueries, setPreviousQueries] = useState<{q: string, a: string}[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");

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
      setPreviousQueries([{ q: query, a: res.data.answer }, ...previousQueries]);
    } catch (err) {
      console.error(err);
      setAnswer("Error retrieving answer");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center p-6">
      <h1 className="text-3xl font-bold mb-4">Welcome! What question do you need to ask?</h1>

      {/* Upload Section */}
      <div className="w-full max-w-md bg-white shadow rounded p-4 mb-6">
        <h2 className="text-xl font-semibold mb-2">Upload Document</h2>
        <input type="file" accept=".pdf,.docx" onChange={handleFileChange} className="mb-2" />
        <button
          onClick={handleUpload}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Upload
        </button>
        {uploadStatus && <p className="text-sm mt-2">{uploadStatus}</p>}
      </div>

      {/* Query Section */}
      <div className="w-full max-w-md bg-white shadow rounded p-4 mb-6">
        <h2 className="text-xl font-semibold mb-2">Ask a Question</h2>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your question..."
          className="w-full border rounded p-2 mb-2"
          rows={3}
        />
        <button
          onClick={handleQuery}
          disabled={loading}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:bg-gray-400"
        >
          {loading ? "Loading..." : "Ask"}
        </button>
      </div>

      {/* Answer Section */}
      <div className="w-full max-w-md bg-white shadow rounded p-4 mb-6">
        <h2 className="text-xl font-semibold mb-2">Answer</h2>
        <div className="min-h-[100px] border rounded p-2">
          {answer ? answer : "Your answer will appear here."}
        </div>
      </div>

      {/* Previous Queries */}
      <div className="w-full max-w-md bg-white shadow rounded p-4 overflow-y-auto max-h-64">
        <h2 className="text-xl font-semibold mb-2">Previous Queries</h2>
        <div className="space-y-2">
          {previousQueries.map((item, idx) => (
            <div key={idx} className="p-2 border rounded">
              <p className="font-semibold">Q: {item.q}</p>
              <p className="text-gray-700">A: {item.a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
