document.getElementById('extract-btn').addEventListener('click', async () => {
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = 'Extracting...';

  // 1. Get the current active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  if (!tab) {
    statusDiv.textContent = 'No active tab found.';
    return;
  }

  // 2. Execute the extraction function inside the target page
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      // This runs inside the webpage context
      return document.documentElement.outerHTML;
    }
  }, (results) => {
    // 3. Handle the result sent back from the page
    if (chrome.runtime.lastError || !results || !results[0]) {
      statusDiv.textContent = 'Error extracting HTML.';
      console.error(chrome.runtime.lastError);
      return;
    }

    const rawHtml = results[0].result;
    
    // 4. Trigger the download sequence
    try {
      downloadHtml(rawHtml, tab.title || 'extracted-page');
      statusDiv.textContent = 'Downloaded successfully!';
    } catch (err) {
      statusDiv.textContent = 'Download failed.';
      console.error(err);
    }
  });
});

// Helper function to convert text to a file download
function downloadHtml(htmlContent, pageTitle) {
  // Clean up the title to make a safe filename
  const safeFilename = pageTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '_raw.html';
  
  const blob = new Blob([htmlContent], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement('a');
  a.href = url;
  a.download = safeFilename;
  document.body.appendChild(a);
  a.click();
  
  // Clean up memory
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}