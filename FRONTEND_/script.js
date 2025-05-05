document.addEventListener('DOMContentLoaded', function() {
    // Get form element
    const analysisForm = document.getElementById('analysis-form');
    const messageInput = document.getElementById('message');
    const resultsSection = document.getElementById('results-section');
    const positiveResult = document.querySelector('.result-card.positive');
    const intermediateResult = document.querySelector('.result-card.intermediate');
    const concerningResult = document.querySelector('.result-card.concerning');
    const driftResult = document.querySelector('.result-card.drift');
    const saveBtns = document.querySelectorAll('.save-btn');
    
    // Add form submit handler
    if (analysisForm) {
      analysisForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        
        if (!message) {
          alert('Please enter a message to analyze.');
          return;
        }
        
        // Show loading state
        const originalButtonText = analysisForm.querySelector('button[type="submit"]').textContent;
        analysisForm.querySelector('button[type="submit"]').textContent = 'Analyzing...';
        
        // Simulate API call with timeout
        fetch('/backend/predict', {  // <-- replace URL if needed
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ "text" : message })
        })
        .then(response => response.json())
        .then(data => {
            // Display results
            resultsSection.style.display = 'grid';
            
            if (data.risk === 'high') {
                positiveResult.style.display = 'none';
                concerningResult.style.display = 'block';
                intermediateResult.style.display = "none";
                driftResult.style.display = "none";
              } 
              else if (data.risk === "medium"){
                positiveResult.style.display = 'none';
                concerningResult.style.display = 'none';
                intermediateResult.style.display = "block";
                driftResult.style.display = "none";
              }
              else if (data.risk === "low"){
                positiveResult.style.display = 'block';
                concerningResult.style.display = 'none';
                intermediateResult.style.display = "none";
                driftResult.style.display = "none";
              }
              else {
                positiveResult.style.display = 'none';
                concerningResult.style.display = 'none';
                intermediateResult.style.display = "none";
                driftResult.style.display = "block";
              }

            // Scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth' });
          
          // Reset button text
          analysisForm.querySelector('button[type="submit"]').textContent = originalButtonText;

          saveBtns.forEach(btn => {
            btn.textContent = 'Save to history';
            btn.disabled = false;
          });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Something went wrong while analyzing. Please try again later.');

            // Reset button text even if error happens
            analysisForm.querySelector('button[type="submit"]').textContent = originalButtonText;
        });
      });
    }
    
    // Update save button handlers to account for intermediate state
    saveBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        this.textContent = 'Saved to history';
        this.disabled = true;
        
        const historyList = document.querySelector('.history-list');
        const noHistory = document.querySelector('.no-history');
        
        if (noHistory) {
          noHistory.style.display = 'none';
        }
        
        // Determine status text based on which result is visible
        let statusText, statusClass;
        if (concerningResult.style.display === 'block') {
          statusText = 'Concerning patterns detected';
          statusClass = 'status-red';
        } else if (intermediateResult.style.display === 'block') {
          statusText = 'Depressing patterns detected';
          statusClass = 'status-yellow';
        } else if (positiveResult.style.display === "block") {
          statusText = 'No concerning patterns';
          statusClass = 'status-green';
        }
        else {
          statusText = "Data Drift detected";
          statusClass = "status-purple"
        }
        
        // Create a history item
      const historyItem = document.createElement('div');
      historyItem.className = 'history-item';
      historyItem.innerHTML = `
        <div class="history-header">
          <div class="history-status">
            <div class="status-dot ${
                concerningResult.style.display === 'block' ? 'status-red' : 
                intermediateResult.style.display === 'block' ? 'status-yellow' : 
                driftResult.style.display === 'block' ? 'status-purple' : 
                'status-green'
            }"></div>
            <span>${
                concerningResult.style.display === 'block' ? 'Concerning patterns detected' : 
                intermediateResult.style.display === 'block' ? 'Depressing patterns detected' : 
                driftResult.style.display === 'block' ? "Data Drift detected" :
                'No concerning patterns'
            }</span>
            </div>
          <span class="history-time">Just now</span>
        </div>
        <p class="history-message">${messageInput.value.substring(0, 60)}${messageInput.value.length > 60 ? '...' : ''}</p>
      `;
        
        // Add styles to the history item
      const style = document.createElement('style');
      style.textContent = `
        .history-item {
          border-bottom: 1px solid var(--border-color);
          padding-bottom: 1rem;
        }
        .history-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.25rem;
        }
        .history-status {
          display: flex;
          align-items: center;
        }
        .status-dot {
          height: 8px;
          width: 8px;
          border-radius: 50%;
          margin-right: 0.5rem;
        }
        .status-green {
          background-color: var(--green-color);
        }
        .status-red {
          background-color: var(--red-color);
        }
        .history-time {
          font-size: 0.75rem;
          color: var(--dark-gray);
        }
        .history-message {
          font-size: 0.875rem;
          color: var(--dark-gray);
          line-clamp: 1;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      `;
      document.head.appendChild(style);
      
      historyList.prepend(historyItem);
    });
  });
});

document.addEventListener('DOMContentLoaded', function() {
  const feedbackForm = document.getElementById('feedback-form');

  feedbackForm.addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent page reload

    const rating = document.getElementById('rating').value;
    const comments = document.getElementById('feedback').value;

    if (rating >= 1 && rating <= 5) {
      try {
        // Prepare the data to send
        const feedbackData = {
          rating: parseInt(rating),
          comments: comments.trim()
        };

        // Call the API
        const response = await fetch('/backend/feedback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(feedbackData)
        });

        if (response.ok) {
          alert('Thank you for your feedback!');
          feedbackForm.reset();
        } else {
          alert('Something went wrong. Please try again.');
        }
      } catch (error) {
        console.error('Error submitting feedback:', error);
        alert('Failed to send feedback. Please check your internet connection.');
      }
    } else {
      alert('Please enter a valid rating between 1 and 5.');
    }
  });
});

document.addEventListener('DOMContentLoaded', function() {
  const classificationForm = document.getElementById('classification-form');

  classificationForm.addEventListener('submit', async function(event) {
    event.preventDefault(); // Stop form from refreshing page

    const message = document.getElementById('message').value.trim();
    const classification = document.getElementById('classification').value;

    if (message && classification) {
      try {
        const payload = {
          text : message,
          label : classification
        };

        const response = await fetch('/backend/diagnostic', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (response.ok) {
          alert('Classification submitted successfully!');
          classificationForm.reset();
        } else {
          alert('Something went wrong. Please try again.');
        }
      } catch (error) {
        console.error('Error submitting classification:', error);
        alert('Failed to submit. Check your network.');
      }
    } else {
      alert('Please fill in all fields.');
    }
  });
});

async function fetchImage(plotName) {

  try {
    const response = await fetch(`/backend/visualizations/${plotName}`);
    const data = await response.json();

    if (!data.image_base64) throw new Error('No image data found in response');

    const imgElement = document.getElementById('modal-image');
    imgElement.src = `data:image/png;base64,${data.image_base64}`;
    imgElement.alt = `Visualization: ${plotName}`;
    document.getElementById('image-modal').style.display = 'flex';

  } catch (error) {
    console.error('Error fetching image:', error);
    document.getElementById('modal-error').textContent = `Failed to load image: ${error.message}`;
    document.getElementById('modal-error').style.display = 'block';
  }
}


function closeModal() {
  document.getElementById('image-modal').style.display = 'none';
}

async function fetchLog(logName) {
  try {
    const response = await fetch(`/backend/logs/${logName}`); // change if needed
    const data = await response.json();

    const logText = data.log_text; // assuming response like { "log_text": "..." }
    const logElement = document.getElementById('modal-log-text');
    logElement.textContent = logText;

    document.getElementById('log-modal').style.display = 'flex';
  } catch (error) {
    console.error('Error fetching log:', error);
  }
}

function closeLogModal() {
  document.getElementById('log-modal').style.display = 'none';
}
