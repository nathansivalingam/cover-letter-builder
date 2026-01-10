import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [pdfUrl, setPdfUrl] = useState(null);
  const [pdfName, setPdfName] = useState("cover_letter.pdf");

  useEffect(() => {
    // Cleanup blob URL on unmount
    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
  }, [pdfUrl]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("resume", file);
      formData.append("job_description", jobDescription);
      formData.append("output", "pdf");

      const res = await fetch("http://localhost:8000/cover-letter", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Request failed");
      }

      const disposition = res.headers.get("content-disposition") || "";
      const match = disposition.match(/filename="?([^"]+)"?/i);
      const filename = match?.[1] || "cover_letter.pdf";
      setPdfName(filename);

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
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
    <div className="page">
      <header className="header">
        <h1 className="title">Cover Letter Builder</h1>
        <p className="subtitle">
          Upload a resume PDF and paste a job description to generate a downloadable cover letter.
        </p>
      </header>

      <main className="grid">
        <section className="card">
          <h2 className="cardTitle">Inputs</h2>

          <form onSubmit={handleSubmit} className="form">
            <label className="label">
              Resume (PDF)
              <div className="fileRow">
                <input
                  className="fileInput"
                  type="file"
                  accept="application/pdf"
                  required
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
                {file && <span className="pill">{file.name}</span>}
              </div>
            </label>

            <label className="label">
              Job description
              <textarea
                className="textarea"
                placeholder="Paste the job description here..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={10}
                required
              />
            </label>

            <div className="actions">
              <button className="button" disabled={loading || !file}>
                {loading ? "Generating…" : "Generate PDF"}
              </button>

              {/*{pdfUrl && (
                <button type="button" className="buttonSecondary" onClick={handleDownload}>
                  Download
                </button>
              )}*/}
            </div>

            {error && <div className="error">{error}</div>}
          </form>
        </section>

        <section className="card">
          <h2 className="cardTitle">Output</h2>

          {!pdfUrl ? (
            <div className="empty">
              <p className="emptyTitle">No PDF yet</p>
              <p className="emptyText">Generate a cover letter to enable the download button.</p>
            </div>
          ) : (
            <div className="output">
              <div className="outputHeader">
                <div>
                  <p className="outputLabel">Ready</p>
                  <p className="outputName">{pdfName}</p>
                </div>
                <button className="buttonSecondary" onClick={handleDownload}>
                  Download PDF
                </button>
              </div>

              {/* Minimal preview box (optional). Uncomment if you want inline viewing. */}
              {/* <iframe className="preview" title="PDF Preview" src={pdfUrl} /> */}
              {/*<div className="hint">
                Tip: if you want an inline preview, uncomment the iframe in <code>App.jsx</code>.
              </div>*/}
            </div>
          )}
        </section>
      </main>

      <footer className="footer">
        <span>
          Authors:{" "}
          <a
            href="https:/https://www.linkedin.com/in/ben-mcmillen-b587b7227//www.linkedin.com/in/ben-mcmillen-b587b7227/"
            target="_blank"
            rel="noopener noreferrer"
          >
            Ben McMillen
          </a>
          {" and "}
          <a
            href="https://www.linkedin.com/in/nathansivalingam/"
            target="_blank"
            rel="noopener noreferrer"
          >
            Nathan Sivalingam
          </a>
        </span>
      </footer>
    </div>
  );
}

export default App;
