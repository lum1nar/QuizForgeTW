document.getElementById("sendBtn").addEventListener("click", sendPrompt);

async function sendPrompt() {
    const prompt = document.getElementById("promptInput").value;
    if (!prompt) {
        alert("請先輸入 prompt");
        return;
    }

    // Clear Response Text
    const output = document.getElementById("response");
    output.textContent = "";

    try {
        const res = await fetch("http://100.74.76.70:8000/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            body: JSON.stringify({ prompt: prompt }),
        });

        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            output.textContent += decoder.decode(value);
        }
    } catch (err) {
        output.textContent = "Error: " + err.message;
    }
}
