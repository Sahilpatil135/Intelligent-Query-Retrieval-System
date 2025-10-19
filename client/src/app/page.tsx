"use client";

import React, { useEffect, useState } from "react";
import axios from "axios";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [previousQueries, setPreviousQueries] = useState<{ q: string, a: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  // const [references, setReferences] = useState<{ source: string; page?: number }[]>([]);
  const [references, setReferences] = useState<string[]>([]);

  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  const [showDocs, setShowDocs] = useState(false);
  // const [userDocs, setUserDocs] = useState<{ name: string; url?: string }[]>([]);
  const [documents, setDocuments] = useState<{ name: string; url: string }[]>([]);

  useEffect(() => {
    // Get current user
    const getUser = async () => {
      const { data } = await supabase.auth.getUser();
      if (!data.user) {
        router.push("/login");  //  redirect to login if not authenticated
      } else {
        setUser(data.user);     // stores user uuid
      }
    };
    getUser();
  }, [router]);

  useEffect(() => {
    const fetchDocuments = async () => {
      if (!user) return;
      setLoading(true);
      try {
        const { data, error } = await supabase
          .from("documents")
          .select("metadata")
          .eq("user_id", user.id);

        if (error) throw error;

        // Extract unique file names + URLs
        const uniqueDocsMap = new Map<string, string>();

        data.forEach((item: any) => {
          const meta = item.metadata || {};
          const fileName = meta.source;
          const fileUrl = meta.file_url;
          if (fileName && !uniqueDocsMap.has(fileName)) {
            uniqueDocsMap.set(fileName, fileUrl);
          }
        });

        const uniqueDocs = Array.from(uniqueDocsMap, ([name, url]) => ({ name, url }));
        setDocuments(uniqueDocs);
      } catch (err) {
        console.error("Error fetching documents:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, [user]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setUser(null);
    router.push("/login");
  };

  if (!user) return <div>Loading...</div>;

  // Function to get the auth token to send to backend
  const getAuthToken = async (): Promise<string | null> => {
    const session = await supabase.auth.getSession();
    return session.data.session?.access_token || null;
  };

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

    try {
      const token = await getAuthToken();
      if (!token) {
        setUploadStatus("User not authenticated. Please log in again.");
        return;
      }

      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", user.id); // send user id to backend

      const res = await axios.post("http://127.0.0.1:5000/upload", formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data"
        },
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
      const token = await getAuthToken();
      if (!token) {
        setAnswer("User not authenticated. Please log in again.");
        return;
      }

      const res = await axios.post("http://127.0.0.1:5000/query", {
        query,
        top_k: 3,
      },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAnswer(res.data.answer);

      // extract unique file names from res.data.references
      const uniqueSources: string[] = Array.from(
        new Set(res.data.references.map((r: any) => {
          // extract filename only, e.g. "DMMM QB IAT-1.pdf"
          const parts = r.source.split(/[/\\]/); // handles / and \
          return parts[parts.length - 1];
        }))
      );

      setReferences(uniqueSources);

      // setReferences(res.data.references || []);
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

  // Function to fetch user's uploaded documents
  // const fetchUserDocuments = async () => {
  //   if (!user?.id) return;
  //   const { data, error } = await supabase
  //     .from("documents") // make sure your table is named 'documents'
  //     .select("metadata->>file_name, metadata->>file_url")
  //     .eq("user_id", user.id);

  //   if (error) {
  //     console.error("Error fetching documents:", error);
  //   } else {
  //     const docs = data.map((doc: any) => ({
  //       name: doc["metadata->>file_name"] || "Unnamed file",
  //       url: doc["metadata->>file_url"] || null,
  //     }));
  //     setUserDocs(docs);
  //   }
  // };

  // // Toggle sidebar
  // const handleToggleDocs = async () => {
  //   if (!showDocs) {
  //     await fetchUserDocuments();
  //   }
  //   setShowDocs(!showDocs);
  // };


  return (
    <div
      className={`min-h-screen bg-gray-900 text-gray-100 flex flex-col items-center px-4 transition-all ${hasHistory ? "justify-start pt-8" : "justify-center"
        }`}
    >
      {/* Header */}
      {/* Sidebar toggle button */}
      {/* <button
        onClick={handleToggleDocs}
        className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-white absolute top-8 left-8 cursor-pointer"
      >
        {showDocs ? "Hide Docs" : "My Documents"}
      </button>

      {/* Sidebar listing *
      {showDocs && (
        <div className="absolute top-20 left-8 bg-gray-800 rounded-xl shadow-lg p-4 w-64 max-h-96 overflow-y-auto border border-gray-700">
          <h3 className="text-lg font-semibold mb-3">Your Documents</h3>
          {userDocs.length === 0 ? (
            <p className="text-gray-400 text-sm">No documents uploaded yet.</p>
          ) : (
            <ul className="space-y-2">
              {userDocs.map((doc, idx) => (
                <li
                  key={idx}
                  className="bg-gray-700 hover:bg-gray-600 rounded-lg p-2 text-sm text-gray-200 cursor-pointer"
                  onClick={() => {
                    if (doc.url) window.open(doc.url, "_blank");
                  }}
                >
                  📄 {doc.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      )} */}

      {/* Sidebar Toggle Button */}
      <button
        onClick={() => setShowDocs((prev) => !prev)}
        className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-white absolute top-8 left-8 cursor-pointer z-20"
      >
        {showDocs ? "Hide Docs" : "My Documents"}
      </button>

      {/* Sidebar List (toggle visible) */}
      {showDocs && (
        <div className="absolute top-20 left-8 bg-gray-800 rounded-xl shadow-lg p-4 w-64 max-h-96 overflow-y-auto border border-gray-700 z-10">
          <h3 className="text-lg font-semibold mb-3">Your Documents</h3>
          {loading ? (
            <p className="text-gray-400 text-sm">Loading...</p>
          ) : documents.length === 0 ? (
            <p className="text-gray-400 text-sm">No documents uploaded yet.</p>
          ) : (
            <ul className="space-y-2">
              {documents.map((doc, idx) => (
                <li
                  key={idx}
                  className="bg-gray-700 hover:bg-gray-600 rounded-lg p-2 text-sm text-gray-200 cursor-pointer"
                  onClick={() => doc.url && window.open(doc.url, "_blank")}
                >
                  📄 {doc.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <button
        onClick={handleLogout}
        className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg text-white absolute top-8 right-8 cursor-pointer"
      >
        Logout
      </button>
      {/* <div className="w-full max-w-5xl flex justify-between items-center mb-6"> */}
      <h1 className="text-2xl font-semibold pt-1 mt-12 mb-6 bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent ">Welcome, {user.email}</h1>
      {/* <button
          onClick={handleLogout}
          className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg text-white"
        >
          Logout
        </button> */}
      {/* </div> */}

      <h1 className="text-4xl font-bold mt-6 mb-6 text-center bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
        Ask Anything
      </h1>

      {/* Upload Section */}
      <div className="w-full max-w-lg bg-gray-800 rounded-2xl shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-3">Upload Document <span className="text-lg font-normal pl-4">(limit 5 Mb)</span></h2>
        <div className="flex items-center justify-between">
          <input
            id="fileUpload"
            type="file"
            accept=".pdf,.docx"
            onChange={handleFileChange}
            className="hidden"
          />
          <label
            htmlFor="fileUpload"
            className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg text-white cursor-pointer"
          >
            Choose File
          </label>
          <button
            onClick={handleUpload}
            className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg text-white cursor-pointer"
          >
            Upload
          </button>
        </div>
        {/* Show selected file name */}
        {file && (
          <p className="text-sm text-gray-300 mt-2">
            Selected: <span className="text-purple-400 font-medium">{file.name}</span>
          </p>
        )}

        {uploadStatus && (
          <p className="text-sm text-gray-300 mt-2">{uploadStatus}</p>
        )}
      </div>

      {/* Chat Section */}
      <div className="w-full max-w-4xl bg-gray-800 rounded-2xl shadow p-6 flex flex-col space-y-4">
        {/* Previous Queries */}
        <div className="flex-1 overflow-y-auto max-h-96 space-y-4 pr-2 custom-scrollbar">
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
                {/* <p>{item.a}</p> */}
                <div
                  className="prose prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: item.a }}
                />
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
            className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg disabled:bg-gray-500 text-white cursor-pointer"
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
          {/* <div className="prose prose-invert max-w-none bg-gray-700 rounded-lg p-4">
            <ReactMarkdown>{answer}</ReactMarkdown>
          </div> */}

          {/* Show references */}
          {references.length > 0 && (
            <div className="mt-4 text-sm text-gray-400">
              <p className="font-semibold">Sources:</p>
              <ul className="list-disc list-inside">
                {/* {references.map((ref, idx) => (
                  <li key={idx}>
                    {ref.source.replace("../data\\", "")}
                  </li>
                ))} */}
                {references.map((src, idx) => (
                  <li key={idx}>{src}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
