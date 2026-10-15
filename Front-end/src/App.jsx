//import { useState } from 'react';
import PostCard from './components/PostCard.jsx';
import './App.css';

// The demo filler data of right and left wing and netural posts
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

export default function App() {
  return (
    <main className="feed-demo">
      <header className="page-heading">
        <p className="project-name">Local Feed Re-Ranker</p>
        <h1>Your feed</h1>
      </header>

      <p className="demo-note">
        Sample posts for interface development.
      </p>

      <section aria-label="Sample feed posts">
        {posts.map((post, index) => (
          <PostCard
            key={post.id}
            post={post}
            rank={index + 1}
          />
        ))}
      </section>
    </main>
  );
}