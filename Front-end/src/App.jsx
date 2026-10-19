import { useState } from 'react';
import PostCard from './components/PostCard.jsx';
import './App.css';

// The demo filler data of right and left wing and netural posts. It includes the post id, name, username, initials, time posted, text, topic, and political lean.
const posts = [
  {
    id: 'post-1',
    name: 'John Smith',
    handle: '@johnsmith',
    initials: 'JS',
    time: '5 mins ago',
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Consequuntur aliquip aute aut qui sit qui quas quaerat enim adipiscing ex. Proident animi numquam dicta esse.',
    topic: 'Transit',
    lean: 'Left',
  },
  {
    id: 'post-2',
    name: 'Jane Smith',
    handle: '@janesmith',
    initials: 'JS',
    time: '12 mins ago',
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    topic: 'Election',
    lean: 'Center',
  },
  {
    id: 'post-3',
    name: 'Doe Smith',
    handle: '@doesmith',
    initials: 'DS',
    time: '25 mins ago',
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Consequuntur aliquip aute aut qui sit qui quas quaerat enim adipiscing ex. Proident animi numquam dicta esse.',
    topic: 'Budget',
    lean: 'Right',
  },
];

const standardPosts = posts;

// A temporary order for the demo posts
// the real reranker is not connected yet.
const balancedDemoPosts = [posts[2], posts[0], posts[1]];

export default function App() {
  const [feedMode, setFeedMode] = useState('standard');

  // If the feed mode is set to standard, then the posts visible are standard. Otherwise, if set to balanced, the posts visible are balanced
  const visiblePosts = feedMode === 'standard'
    ? standardPosts
    : balancedDemoPosts;

  // Displays the posts in the feed
  // .map function iterates the array and creates a PostCard component for each post.
  return (
    <main className="feed-demo">
      <header className="page-heading">
        <p className="project-name">Local Feed Re-Ranker</p>
        <h1>Your feed</h1>
      </header>

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
          ? 'Standard feed: sample demo posts.'
          : 'Balanced feed: predefined order. Reranker not connected yet.'}
      </p>

      <section aria-label={`${feedMode} feed posts`}>
        {visiblePosts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
          />
        ))}
      </section>
    </main>
  );
}