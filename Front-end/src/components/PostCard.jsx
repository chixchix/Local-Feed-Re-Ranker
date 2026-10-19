export default function PostCard({ post }) {
  return (
    <article className="post">
      <div className="post-avatar" aria-hidden="true">{post.initials}</div>

      <div className="post-content">
        <header className="post-header">
          <div>
            <div className="post-identity">
              <h2>{post.name}</h2>
              <span className="post-handle">{post.handle}</span>
            </div>
            <p className="post-time">{post.time}</p>
          </div>
        </header>

        <p className="post-text">{post.text}</p>

        <footer className="post-tags">
          <span className="topic-tag">{post.topic}</span>
          <span className="lean-tag">Lean: {post.lean}</span>
        </footer>
      </div>
    </article>
  );
}
