/**
 * Creates a slider component that adjusts the diversity weight of the feed.
 * Slider with a range of 0 to 1, step of 0.05, and displays the current value selected.
 */

export default function DiversitySlider({ value, onChange, appliedValue, onApply, isBalanced }) {
    const hasChanges = value !== appliedValue;
  return (
    <aside className="diversity-panel">
      <h2>Feed diversity</h2>

      <div className="diversity-label">
        <label htmlFor="diversity-weight">
          Diversity weight
        </label>

        {/* Displays the current value of slider with 2 decimal places */}
        <output htmlFor="diversity-weight">
          {value.toFixed(2)}
        </output>
      </div>

        {/* Slider with a range of 0 to 1 that adjusts in increments of 0.05 */}
      <input
        id="diversity-weight"
        className="diversity-slider"
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={value}
        disabled ={!isBalanced} // Disables the slider if the feed is not in balanced mode

        onChange={(event) => {
          onChange(Number(event.target.value)); // Retrieves slider's value and converts it to a number before its passed to update the state
        }}
        aria-describedby="diversity-description"
      />

      <div className="diversity-endpoints">
        <span>Lower</span>
        <span>Higher</span>
      </div>

      {/* <p id="diversity-description">
        Higher values give more weight to diversity.
      </p> */}

      <button
        type="button"
        className="apply-diversity"
        disabled={!isBalanced || !hasChanges}
        onClick={onApply}
      >
        Apply changes
      </button>

      <p id="diversity-status" aria-live="polite">
        {!isBalanced
          ? 'Switch to Balanced feed to adjust diversity.'
          : hasChanges
            ? 'You have unapplied changes.'
            : 'Your setting is up to date.'}
      </p>

      <p className="diversity-applied">
        Applied setting: {appliedValue.toFixed(2)}
      </p>

      <p className="diversity-demo-note">
        Preview control only. Feed reranking is not connected yet.
      </p>
    </aside>
  );
}