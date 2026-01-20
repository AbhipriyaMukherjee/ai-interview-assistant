let mediaRecorder;
let recordedChunks = [];
let stream;

/**
 * Initializes the camera and microphone stream.
 */
async function startInterview() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        const videoElement = document.getElementById('video-preview');
        videoElement.srcObject = stream;

        recordedChunks = [];
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        mediaRecorder.start();
        console.log("Recording started...");
        
        // Update UI state
        document.getElementById('start-btn').disabled = true;
        document.getElementById('stop-btn').disabled = false;
        document.getElementById('status-note').innerText = "Recording in progress...";
    } catch (err) {
        console.error("Error accessing media devices:", err);
        alert("Could not access camera/microphone. Please check permissions.");
    }
}

/**
 * Stops recording and sends the multi-modal data to the server.
 */
async function stopRecording() {
    if (!mediaRecorder) return;

    mediaRecorder.stop();
    mediaRecorder.onstop = async () => {
        // Stop all camera/mic tracks to release hardware
        stream.getTracks().forEach(track => track.stop());

        const videoBlob = new Blob(recordedChunks, { type: 'video/webm' });
        const formData = new FormData();

        // Pulling dynamic data from the hidden inputs or text elements in interview_live.html
        const role = document.getElementById('role-title').innerText;
        const questionText = document.getElementById('question-text').innerText;

        formData.append('video', videoBlob, 'interview.webm');
        formData.append('role', role);
        formData.append('question_text', questionText);

        // Update UI to show processing state
        document.getElementById('status-note').innerText = "AI is analyzing your performance... please wait.";
        document.getElementById('stop-btn').disabled = true;

        try {
            const response = await fetch('/submit_interview', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                // Redirect to the feedback page using the ID returned by the server
                window.location.href = `/feedback?id=${data.id}`;
            } else {
                throw new Error("Server analysis failed");
            }
        } catch (error) {
            console.error("Submission error:", error);
            document.getElementById('status-note').innerText = "Error: Could not save interview.";
            document.getElementById('start-btn').disabled = false;
        }
    };
}

// Event Listeners for buttons
document.getElementById('start-btn').addEventListener('click', startInterview);
document.getElementById('stop-btn').addEventListener('click', stopRecording);
