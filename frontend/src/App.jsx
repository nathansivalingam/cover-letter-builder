import { useEffect, useState } from "react";
import "./App.css";

// ✅ Render PDF pages to IMAGES using pdfjs-dist (no iframe / no react-pdf)
import * as pdfjsLib from "pdfjs-dist";
import pdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";

// ✅ Vite-friendly worker setup
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

function App() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [template, setTemplate] = useState("classic");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Download link
  const [pdfUrl, setPdfUrl] = useState(null);
  const [pdfName, setPdfName] = useState("cover_letter.pdf");

  // Image preview state
  const [pageImages, setPageImages] = useState([]);
  const [renderingPreview, setRenderingPreview] = useState(false);

  useEffect(() => {
    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
  }, [pdfUrl]);

  async function renderPdfToImages(blob) {
    setRenderingPreview(true);
    setPageImages([]);

    try {
      const data = await blob.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data }).promise;

      const images = [];
      for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        const page = await pdf.getPage(pageNum);

        // Quality control: 1.4–2.0 is usually good
        const viewport = page.getViewport({ scale: 1.6 });

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        canvas.width = Math.floor(viewport.width);
        canvas.height = Math.floor(viewport.height);

        await page.render({ canvasContext: ctx, viewport }).promise;

        images.push(canvas.toDataURL("image/png"));
      }

      setPageImages(images);
    } catch (e) {
      console.error(e);
      setError("Preview render failed (PDF -> images).");
    } finally {
      setRenderingPreview(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    // reset previous output
    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }
    setPageImages([]);

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("resume", file);
      formData.append("job_description", jobDescription);
      formData.append("output", "pdf");
      formData.append("template", template);

      const res = await fetch("http://127.0.0.1:8000/cover-letter", {
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

      // Download URL
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);

      // Preview images
      await renderPdfToImages(blob);
    } catch (err) {
      setError(err?.message || "Something went wrong");
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
              Template
              <select
                className="select"
                value={template}
                onChange={(e) => setTemplate(e.target.value)}
              >
                <option value="classic">Classic</option>
                <option value="minimal">Minimal</option>
              </select>
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
              <div className="previewWrap">
                <div className="previewBar">Preview</div>

                <div className="imagePreview">
                  {renderingPreview ? (
                    <div className="pdfLoading">Rendering preview…</div>
                  ) : pageImages.length === 0 ? (
                    <div className="pdfError">Preview not available.</div>
                  ) : (
                    pageImages.map((src, i) => (
                      <img
                        key={i}
                        className="pdfPageImg"
                        src={src}
                        alt={`PDF page ${i + 1}`}
                        loading="lazy"
                      />
                    ))
                  )}
                </div>
              </div>
              <div className="outputHeader">
                <div>
                  <p className="outputLabel">Ready</p>
                  <p className="outputName">{pdfName}</p>
                </div>
                <button type="button" className="buttonSecondary" onClick={handleDownload}>
                  Download PDF
                </button>
              </div>
            </div>
          )}
        </section>
      </main>

      <footer className="footer">
        <span>
          Authors:{" "}
          <a
            href="https://www.linkedin.com/in/ben-mcmillen-b587b7227/"
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
