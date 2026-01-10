import { useState } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // store the generated PDF url + filename
  const [pdfUrl, setPdfUrl] = useState(null);
  const [pdfName, setPdfName] = useState("cover_letter.pdf");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    // clear any previous pdf url to avoid leaks
    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("resume", file);
      formData.append("job_description", jobDescription);
      formData.append("output", "pdf"); // backend must support this

      const res = await fetch("http://localhost:8000/cover-letter", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Request failed");
      }

      // Get filename if backend provides it
      const disposition = res.headers.get("content-disposition") || "";
      const match = disposition.match(/filename="?([^"]+)"?/i);
      const filename = match?.[1] || "cover_letter.pdf";
      setPdfName(filename);

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);

      // Don’t open automatically — just store it for the download button
      setPdfUrl(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleDownload() {
    if (!pdfUrl) return;

    const a = document.createElement("a");
    a.href = pdfUrl;
    a.download = pdfName;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>Cover Letter Generator</h1>

      <form onSubmit={handleSubmit}>
        <div>
          <input
            type="file"
            accept="application/pdf"
            required
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>

        <div style={{ marginTop: 12 }}>
          <textarea
            placeholder="Paste job description here..."
            rows={10}
            style={{ width: "100%" }}
            required
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
          />
        </div>

        <button style={{ marginTop: 12 }} disabled={loading || !file}>
          {loading ? "Generating..." : "Generate Cover Letter PDF"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {pdfUrl && (
        <div style={{ marginTop: 16 }}>
          <p>PDF ready: <strong>{pdfName}</strong></p>
          <button onClick={handleDownload}>Download PDF</button>

          {/* Optional: show an inline preview */}
          {/* <div style={{ marginTop: 12 }}>
            <iframe title="pdf-preview" src={pdfUrl} width="100%" height="500" />
          </div> */}
        </div>
      )}
    </div>
  );
}

export default App;
