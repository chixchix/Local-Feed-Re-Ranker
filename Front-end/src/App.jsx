import { useState, useEffect } from 'react';
import PostCard from './components/PostCard.jsx';
import DiversitySlider from './components/DiversitySlider.jsx';
import './App.css';
import { fetchFeed } from './api.js';

// Converts the numerical stance values of -1 - 1 to the corresponding stance labels for display
function stanceToLabel(stance) {
  const labels = {
    '-1': 'Left',
    '-0.5': 'Lean Left',
    '0': 'Center',
    '0.5': 'Lean Right',
    '1': 'Right',
  };

  return labels[String(stance)] ?? 'Unknown';
}

// Manages the state of the feed (feed mode, diversity weight, applied weight, visible posts, etc) and handles the fetching of posts
export default function App() {
  const [feedMode, setFeedMode] = useState('standard');
  const [diversityWeight, setDiversityWeight] = useState(0.5); // set to 0.5 as the default value for the diversity weight when app is loaded
  const [appliedWeight, setAppliedWeight] = useState(0.5); // set to 0.5 as the default for the applied weight

  const [visiblePosts, setVisiblePosts] = useState([]); // stores the visible posts to display on feed
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

// Fetches the feed posts when the feed more or weights change
// Updates the visible posts
useEffect(() => {
  let cancelled = false;

  async function loadFeed() {
    setLoading(true);
    setError(null);

    try {
      const posts = await fetchFeed(feedMode, appliedWeight); // Fetches posts from the backend

      // Maps the fetched posts to the postcard component. to be changed in the future to include more data
      if (!cancelled) {
        const mappedPosts = posts.map((post, index) => ({
          id: post.id ?? `post-${index}`,
          name: post.name ?? 'News Source',
          handle: post.handle ?? '@news',
          initials: post.initials ?? 'NS',
          time: post.time ?? '',
          text: post.text ?? '',
          topic: post.topic ?? 'General',
          lean: stanceToLabel(post.stance),
        }));

        setVisiblePosts(mappedPosts);

      }
    } catch (err) {
      if (!cancelled) {
        setError(err.message);
        setVisiblePosts([]);
      }
    } finally {
      if (!cancelled) {
        setLoading(false);
      }
    }
  }

  loadFeed();

  return () => {
    cancelled = true;
  };
}, [feedMode, appliedWeight]);

  // Handles the application of the diversity weight when the "Apply changes" button is clicked
  function handleApply() {
      if (feedMode !== 'balanced') {
        return;
      }

    setAppliedWeight(diversityWeight); // updates the applied weight to tthe current weight when button is clicked
  }
  // Displays the posts in the feed
  // .map function iterates the array and creates a PostCard component for each post.
  return (
    <main className="feed-demo">
      <header className="page-heading">
        <p className="project-name">Local Feed Re-Ranker</p>
        <h1>Your feed</h1>
      </header>

      <div className="feed-layout">
        <div className="feed-column">
          <div className="feed-toolbar">
            <div
              className="feed-switch"
              role="group"
              aria-label="Choose feed view"
            >
              <button
                type="button"
                aria-pressed={feedMode === 'standard'}
                onClick={() => setFeedMode('standard')}
              >
                Standard feed
              </button>

              <button
                type="button"
                aria-pressed={feedMode === 'balanced'}
                onClick={() => setFeedMode('balanced')}
              >
                Balanced feed
              </button>
            </div>
          </div>

          <p className="demo-note" aria-live="polite">
            {feedMode === 'standard'
              ? 'Standard feed'
              : `Balanced feed - diversity weight: ${appliedWeight.toFixed(2)}`}
          </p>

          <section aria-label={`${feedMode} feed posts`}>
            {loading && <p>Loading feed...</p>}
            {error && <p role="alert">Error: {error}</p>}
            {!loading && !error && visiblePosts.length === 0 && (
            <p>No posts available.</p>
  )}
            {!loading && !error && visiblePosts.map((post) => (
              <PostCard
                key={post.id}
                post={post}
              />
            ))}
          </section>
        </div>
        <DiversitySlider
              value={diversityWeight}
              onChange={setDiversityWeight}
              appliedValue={appliedWeight}
              onApply={handleApply}
              isBalanced={feedMode === 'balanced'}
            />
      </div>
    </main>
  );
}