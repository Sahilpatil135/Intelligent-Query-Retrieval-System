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
        <div className="flex flex-col items-center gap-4 p-8">
            <h1 className="text-2xl font-bold">Login / Sign Up</h1>
            <input type="email" placeholder="Email" className="border p-2 rounded w-64" value={email} onChange={(e) => setEmail(e.target.value)} />
            <input type="password" placeholder="Password" className="border p-2 rounded w-64" value={password} onChange={(e) => setPassword(e.target.value)} />
            <div className="flex gap-2">
                <button onClick={handleLogin} className="bg-blue-600 text-white px-4 py-2 rounded">
                    Login
                </button>
                <button onClick={handleSignup} className="bg-green-600 text-white px-4 py-2 rounded">
                    Sign Up
                </button>
            </div>

            <p className="text-sm text-gray-600">{message}</p>
        </div>
    );
}



