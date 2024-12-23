"use client";

import { useState } from "react";
import axios from "axios";

export default function Home() {
  const [url, setUrl] = useState("");
  const [qrCodeUrl, setQrCodeUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState(""); // For handling existing QR code messages
  const [imgError, setImgError] = useState(false); // Track if the image failed to load

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage(""); // Reset the message
    try {
      const response = await axios.post("http://localhost:8000/generate-qr/", {
        url: url,
      });

      console.log("QR code URL:", response.data.qr_code_url); // Log the URL

      // If the response contains a message, display it
      if (response.data.message) {
        setMessage(response.data.message);
      }

      setQrCodeUrl(response.data.qr_code_url); // Set the QR code URL
    } catch (error) {
      console.error("Error generating QR Code:", error);
      setError("Failed to generate QR Code. Please try again.");
    } finally {
      setLoading(false);
    }
};


  const handleImageError = () => {
    setImgError(true); // Set flag to true when image fails to load
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>QR Code Generator</h1>
      <form onSubmit={handleSubmit} style={styles.form}>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter URL like https://example.com"
          style={styles.input}
        />
        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? "Generating..." : "Generate QR Code"}
        </button>
      </form>
      
      {/* Display the message if QR code exists */}
      {message && <p style={styles.message}>{message}</p>} 
      
      {error && <p style={styles.error}>{error}</p>}
      
      {/* Display QR code */}
      {qrCodeUrl && !message && (
    <div>
        <img src={qrCodeUrl} alt="QR Code" style={styles.qrCode} />
    </div>
)}


      {/* Show error message if image fails to load */}
      {imgError && <p style={styles.error}>Failed to load QR code image.</p>}
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#121212",
    color: "white",
  },
  title: {
    margin: "0",
    lineHeight: "1.15",
    fontSize: "4rem",
    textAlign: "center",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  input: {
    padding: "10px",
    borderRadius: "5px",
    border: "none",
    marginTop: "20px",
    width: "300px",
    color: "#121212",
  },
  button: {
    padding: "10px 20px",
    marginTop: "20px",
    border: "none",
    borderRadius: "5px",
    backgroundColor: "#0070f3",
    color: "white",
    cursor: "pointer",
  },
  qrCode: {
    marginTop: "20px",
    width: "200px",
    height: "200px",
  },
  error: {
    color: "red",
    marginTop: "20px",
  },
  message: {
    color: "green",
    marginTop: "20px",
  },
};
