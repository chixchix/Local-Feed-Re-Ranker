// FastAPI backend URL on port 8000 to fetch data from backend
const API_URL = 'http://127.0.0.1:8000';

// Fetches posts from backend based on the feed mode and what the diversity weight is set to
export async function fetchFeed(mode, weight = 0.5) {
  const params = new URLSearchParams({
    mode,
    weight: String(weight),
  });

  // Sends a GET request to the /feed endpoint
  const response = await fetch(
    `${API_URL}/feed?${params}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch feed: ${response.status}`);
  }

  const data = await response.json();
  return data.posts;
}
