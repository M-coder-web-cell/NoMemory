document.getElementById('extract-btn').addEventListener('click', async () => {
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = 'Optimizing HTML...';

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  if (!tab) {
    statusDiv.textContent = 'No active tab found.';
    return;
  }

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      // 1. Clone the body context to avoid breaking the live site
      const bodyClone = document.body.cloneNode(true);

      // 2. Immediate hard-removal of absolute script/style junk
      const toxicTrash = 'script, style, svg, link, iframe, noscript, img, video, audio';
      bodyClone.querySelectorAll(toxicTrash).forEach(el => el.remove());

      // 3. Platform-specific target selectors (ChatGPT, Claude, Gemini chat regions)
      // If any of these are found, we pull just that container to avoid sidebars
      const chatSelectors = [
        '#subcontainer',                     // Common app wrappers
        '[role="presentation"]',              // Chat thread areas
        '.conversation-container',
        'main', 
        'article'
      ];
      
      let coreContent = null;
      for (const selector of chatSelectors) {
        const found = bodyClone.querySelector(selector);
        // Make sure it actually contains text before committing to it
        if (found && found.innerText.trim().length > 100) {
          coreContent = found;
          break;
        }
      }

      // Fallback: If no targeted chat container matches, use the pruned body clone
      if (!coreContent) {
        coreContent = bodyClone;
      }

      // 4. Clean attributes smoothly without breaking the DOM tree
      const allElements = coreContent.querySelectorAll('*');
      allElements.forEach(el => {
        // Strip the massive token hogs
        el.removeAttribute('class');
        el.removeAttribute('style');
        el.removeAttribute('data-testid');
        el.removeAttribute('aria-hidden');
        
        // Strip unnecessary interactive states
        el.removeAttribute('disabled');
        el.removeAttribute('tabindex');
      });

      // 5. Safe HTML string extraction
      const finalHtml = coreContent.innerHTML.trim();

      // Final sanity check: If we broke something and it's empty, return raw inner text 
      if (!finalHtml || finalHtml === '') {
        return `<div>${bodyClone.innerText}</div>`;
      }

      return finalHtml;
    }
  }, (results) => {
    if (chrome.runtime.lastError || !results || !results[0]) {
      statusDiv.textContent = 'Error pruning HTML.';
      console.error(chrome.runtime.lastError);
      return;
    }

    const cleanHtml = results[0].result;
    
    try {
      downloadHtml(cleanHtml, tab.title || 'clean-conversation');
      statusDiv.textContent = 'Downloaded Clean HTML!';
    } catch (err) {
      statusDiv.textContent = 'Download failed.';
      console.error(err);
    }
  });
});

function downloadHtml(htmlContent, pageTitle) {
  const safeFilename = pageTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '_clean.html';
  const blob = new Blob([htmlContent], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement('a');
  a.href = url;
  a.download = safeFilename;
  document.body.appendChild(a);
  a.click();
  
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}