from src.core.state import doc_manager, indexer
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter()

@router.get("/upload", response_class=HTMLResponse)
def upload_form():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Upload Document - local-ref-chat</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background: #f0f4f8;
            }
            .upload-container {
                background: white;
                padding: 2rem 3rem;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                width: 350px;
                text-align: center;
            }
            h3 {
                margin-bottom: 1.5rem;
                color: #333;
            }
            input[type="file"] {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 0.5rem;
                width: 100%;
                margin-bottom: 1rem;
            }
            button {
                background: #0078d7;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 0.75rem 1.5rem;
                cursor: pointer;
                width: 100%;
                transition: background 0.3s ease;
            }
            button:hover {
                background: #005ea2;
            }
            #message {
                margin-top: 1rem;
                font-weight: 600;
            }
            #message.success {
                color: green;
            }
            #message.error {
                color: red;
            }
        </style>
    </head>
    <body>
        <div class="upload-container">
            <h3>Upload a PDF or TXT File</h3>
            <input type="file" id="fileInput" accept=".pdf,.txt" />
            <button onclick="uploadFile()">Upload</button>
            <div id="message"></div>
        </div>

        <script>
            async function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                const messageDiv = document.getElementById('message');

                if (!fileInput.files.length) {
                    messageDiv.textContent = "Please select a file to upload.";
                    messageDiv.className = "error";
                    return;
                }

                const file = fileInput.files[0];
                const formData = new FormData();
                formData.append("file", file);

                try {
                    messageDiv.textContent = "Uploading...";
                    messageDiv.className = "";

                    const response = await fetch('/upload_ajax', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || "Upload failed");
                    }

                    const data = await response.json();
                    messageDiv.textContent = `Success: ${data.message}`;
                    messageDiv.className = "success";

                    fileInput.value = "";
                } catch (error) {
                    messageDiv.textContent = `Error: ${error.message}`;
                    messageDiv.className = "error";
                }
            }
        </script>
    </body>
    </html>
    """

@router.post("/upload_ajax")
async def upload_file_ajax(file: UploadFile = File(...)):
    doc_manager.save_uploaded_file(file)
    indexer.rebuild(doc_manager)
    return JSONResponse(content={"filename": file.filename, "message": "File uploaded and indexed successfully."})
