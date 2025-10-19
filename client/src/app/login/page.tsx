"use client";
import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";

export default function AuthPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");
    const router = useRouter();

    const handleSignup = async () => {
        const { error } = await supabase.auth.signUp({ email, password });
        setMessage(error ? error.message : "Signup successful! Please check your email to confirm your account.");
    };

    const handleLogin = async () => {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) setMessage(error.message);
        else {
            setMessage("Login successful!");
            router.push("/"); // Redirect to main page after login
        }
    };

    return (
        // <div className="flex flex-col items-center gap-4 p-8">
        //     <h1 className="text-2xl font-bold">Login / Sign Up</h1>
        //     <input type="email" placeholder="Email" className="border p-2 rounded w-64" value={email} onChange={(e) => setEmail(e.target.value)} />
        //     <input type="password" placeholder="Password" className="border p-2 rounded w-64" value={password} onChange={(e) => setPassword(e.target.value)} />
        //     <div className="flex gap-2">
        //         <button onClick={handleLogin} className="bg-blue-600 text-white px-4 py-2 rounded">
        //             Login
        //         </button>
        //         <button onClick={handleSignup} className="bg-green-600 text-white px-4 py-2 rounded">
        //             Sign Up
        //         </button>
        //     </div>

        //     <p className="text-sm text-gray-600">{message}</p>
        // </div>
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1e1e2f] to-[#11121a] p-4">
            <div className="bg-[#1f1f2f] p-8 rounded-2xl shadow-lg w-full max-w-md">
                <h1 className="text-3xl font-bold text-center text-purple-400 mb-6">Welcome Back</h1>
                
                <input
                    type="email"
                    placeholder="Email"
                    className="w-full mb-4 p-3 rounded-lg bg-[#2b2b3f] text-white border border-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                
                <input
                    type="password"
                    placeholder="Password"
                    className="w-full mb-6 p-3 rounded-lg bg-[#2b2b3f] text-white border border-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />

                <div className="flex gap-4">
                    <button
                        onClick={handleLogin}
                        className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg transition cursor-pointer"
                    >
                        Login
                    </button>
                    <button
                        onClick={handleSignup}
                        className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg transition cursor-pointer"
                    >
                        Sign Up
                    </button>
                </div>

                {message && (
                    <p className="mt-4 text-center text-sm text-gray-300">{message}</p>
                )}
            </div>
        </div>
    );
}



