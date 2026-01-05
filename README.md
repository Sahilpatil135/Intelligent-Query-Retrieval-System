# Intelligent Query-Retrieval System
[![Ask DeepWiki](https://devin.ai/assets/askdeepwiki.png)](https://deepwiki.com/Sahilpatil135/Intelligent-Query-Retrieval-System)

This project is an LLM-powered system that allows users to upload their documents and ask questions about the content. It leverages a Retrieval-Augmented Generation (RAG) architecture, using a vector database to find relevant document chunks and a Large Language Model (LLM) to generate context-aware answers.

The application features a secure, multi-tenant design where each user's documents are stored and queried in isolation.

## Features

- **Secure User Authentication**: Employs Supabase for robust user signup, login, and session management.
- **Private Document Storage**: Each user's documents are stored securely in a private Supabase Storage bucket and are only accessible by them.
- **Vector-Based Retrieval**: Uploaded documents (PDF, DOCX) are chunked, converted into vector embeddings using `sentence-transformers`, and stored in a Supabase PostgreSQL database with the `pgvector` extension.
- **Retrieval-Augmented Generation (RAG)**: When a user asks a question, the system retrieves the most relevant document chunks for that user and feeds them as context to Google's Gemini model to generate an accurate, source-grounded answer.
- **Interactive Frontend**: A web interface built with Next.js and React allows users to manage documents, ask questions, and view their conversation history.
- **Source Referencing**: The generated answers include references to the source documents used to formulate the response.

## Architecture

The system is composed of two main components: a client-side application and a server-side API.

-   **Frontend (Client)**: A [Next.js](https://nextjs.org/) application serves as the user interface. It handles user authentication through Supabase Auth and provides the interface for uploading documents and interacting with the Q&A system. It communicates with the backend via REST API calls, passing along the user's JWT for authentication.

-   **Backend (Server)**: A [Flask](https://flask.palletsprojects.com/) (Python) server that exposes two main endpoints:
    -   `/upload`: Verifies the user's JWT, processes uploaded files (PDF, DOCX), chunks the text, generates embeddings, and stores the file and its vector data in Supabase.
    -   `/query`: Verifies the user, retrieves relevant document chunks from the vector store based on the user's query and `user_id`, and uses the Gemini API to generate a natural language answer.

-   **Supabase**: Used as the all-in-one backend-as-a-service for:
    -   **Authentication**: Manages user accounts and JWT generation.
    -   **Storage**: Stores uploaded documents in a private bucket.
    -   **Database (Postgres with pgvector)**: Stores document chunks and their corresponding vector embeddings for efficient similarity search.

## Technical Stack

-   **Frontend**: Next.js, React, Tailwind CSS, an Axios
-   **Backend**: Flask, Gunicorn
-   **Vector Embeddings**: `sentence-transformers` (all-MiniLM-L6-v2)
-   **LLM**: Google Gemini
-   **Database & Auth**: Supabase

## Setup and Installation

Follow these steps to set up and run the project locally.

### Prerequisites

-   Python 3.8+ and Pip
-   Node.js and npm (or a similar package manager)
-   A Supabase account
-   A Google Gemini API key

### 1. Supabase Project Setup

1.  **Create a Project**: Go to [Supabase](https://supabase.com) and create a new project.
2.  **Get API Keys**: In your project dashboard, go to **Project Settings** > **API**. You will need the **Project URL** and the `anon` **public key** for the client, and the `service_role` **secret key** for the server.
3.  **Get JWT Secret**: Go to **Project Settings** > **API** > **JWT Settings** and copy the **JWT Secret**.
4.  **Create Storage Bucket**: Go to the **Storage** section and create a new **private** bucket named `documents`.
5.  **Database Setup**: Go to the **SQL Editor** and run the following queries to set up the `pgvector` extension, the `documents` table, and the search function.

    ```sql
    -- Enable the pgvector extension
    create extension if not exists vector with schema extensions;

    -- Create the documents table to store chunks and embeddings
    create table documents (
      id bigserial primary key,
      user_id uuid references auth.users not null,
      content text,
      metadata jsonb,
      embedding vector(384) -- Dimension for 'all-MiniLM-L6-v2' model
    );

    -- Create the RPC function for matching documents based on vector similarity
    create or replace function match_documents (
      query_embedding vector(384),
      match_count int,
      filter_user_id uuid
    ) returns table (
      id bigint,
      content text,
      metadata jsonb,
      embedding vector(384),
      similarity float
    )
    language plpgsql
    as $$
    begin
      return query
      select
        id,
        content,
        metadata,
        embedding,
        1 - (documents.embedding <=> query_embedding) as similarity
      from documents
      where documents.user_id = filter_user_id
      order by documents.embedding <=> query_embedding
      limit match_count;
    end;
    $$;
    ```

### 2. Backend Server Setup

1.  Navigate to the `server/` directory.

    ```bash
    cd server
    ```

2.  Create and activate a Python virtual environment.

    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  Install the required Python packages.

    ```bash
    pip install -r requirements.txt
    ```

4.  Create a `.env` file in the `server/` directory and add your credentials:

    ```env
    # Supabase credentials
    SUPABASE_URL="YOUR_SUPABASE_PROJECT_URL"
    SUPABASE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"
    SUPABASE_SERVICE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY" # Duplicated for compatibility
    SUPABASE_JWT_SECRET="YOUR_SUPABASE_JWT_SECRET"

    # LLM API Key
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```

5.  Run the Flask server.
    ```bash
    flask run
    ```
    The backend will be running at `http://127.0.0.1:5000`.

### 3. Frontend Client Setup

1.  In a new terminal, navigate to the `client/` directory.

    ```bash
    cd client
    ```

2.  Install the required npm packages.

    ```bash
    npm install
    ```

3.  Create a `.env.local` file in the `client/` directory and add your public Supabase credentials:

    ```env
    NEXT_PUBLIC_SUPABASE_URL="YOUR_SUPABASE_PROJECT_URL"
    NEXT_PUBLIC_SUPABASE_ANON_KEY="YOUR_SUPABASE_ANON_PUBLIC_KEY"
    ```

4.  Run the Next.js development server.

    ```bash
    npm run dev
    ```

    The application will be available at `http://localhost:3000`. You can now sign up, log in, and start using the system.
